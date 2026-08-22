"""Test deploy plan rendering (no AWS calls)."""

from argparse import Namespace

from python_pivot import deploy


def _args(**overrides):
    values = {
        "function": "f",
        "alias": "live",
        "runtime": "python3.12",
        "stages": "100",
        "dwell": "1",
        "alarm": "alarm1",
        "profile": None,
        "region": None,
        "plan_only": False,
        "apply": True,
    }
    values.update(overrides)
    return Namespace(**values)


class _ResourceNotFound(Exception):
    pass


class _Waiter:
    def wait(self, **kwargs):
        return None


class _Lambda:
    class exceptions:
        ResourceNotFoundException = _ResourceNotFound

    def __init__(self, *, alias=None):
        self.alias = alias
        self.configuration_updates = []
        self.alias_updates = []

    def get_alias(self, **kwargs):
        if self.alias is None:
            raise _ResourceNotFound()
        return self.alias

    def update_function_configuration(self, **kwargs):
        self.configuration_updates.append(kwargs)

    def get_waiter(self, name):
        assert name == "function_updated_v2"
        return _Waiter()

    def publish_version(self, **kwargs):
        return {"Version": "2"}

    def update_alias(self, **kwargs):
        self.alias_updates.append(kwargs)


class _CloudWatch:
    def __init__(self, states):
        self.states = iter(states)

    def describe_alarms(self, **kwargs):
        state = next(self.states)
        if isinstance(state, Exception):
            raise state
        return {"MetricAlarms": [{"AlarmName": "alarm1", "StateValue": state}]}


def test_build_plan_includes_all_stages():
    plan = deploy.build_plan(
        "myfn", "live", [5, 25, 50, 100], 60, "arn:aws:...:MyAlarm", "python3.12"
    )
    assert "myfn" in plan
    assert "python3.12" in plan
    assert "5%" in plan
    assert "25%" in plan
    assert "100%" in plan


def test_build_plan_mentions_rollback():
    plan = deploy.build_plan("f", "live", [10, 100], 30, "alarm1", "python3.12")
    assert "rollback" in plan.lower()


def test_build_plan_warns_without_alarm():
    plan = deploy.build_plan("f", "live", [10, 100], 30, None, "python3.12")
    assert "REFUSE" in plan or "none" in plan


def test_plan_only_prints_and_exits(capsys):
    args = Namespace(
        function="f",
        alias="live",
        runtime="python3.12",
        stages="5,50,100",
        dwell="30",
        alarm=None,
        profile=None,
        region=None,
        plan_only=True,
        apply=False,
    )
    rc = deploy.run(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Canary deployment plan" in out


def test_apply_without_alarm_fails(capsys):
    args = Namespace(
        function="f",
        alias="live",
        runtime="python3.12",
        stages="5,100",
        dwell="10",
        alarm=None,
        profile=None,
        region=None,
        plan_only=False,
        apply=True,
    )
    rc = deploy.run(args)
    assert rc == 2


def test_invalid_stages_fail_before_aws(monkeypatch):
    monkeypatch.setattr(
        deploy,
        "_get_lambda_client",
        lambda *args: (_ for _ in ()).throw(AssertionError("AWS should not be called")),
    )
    assert deploy.run(_args(stages="5,101")) == 2
    assert deploy.run(_args(stages="50,25,100")) == 2
    assert deploy.run(_args(stages="5,50")) == 2


def test_missing_alias_fails_before_function_mutation(monkeypatch):
    lam = _Lambda(alias=None)
    monkeypatch.setattr(deploy, "_get_lambda_client", lambda *args: lam)
    monkeypatch.setattr(deploy, "_get_cw_client", lambda *args: _CloudWatch(["OK"]))

    assert deploy.run(_args()) == 2
    assert lam.configuration_updates == []


def test_unhealthy_alarm_fails_before_function_mutation(monkeypatch):
    lam = _Lambda(alias={"FunctionVersion": "1"})
    monkeypatch.setattr(deploy, "_get_lambda_client", lambda *args: lam)
    monkeypatch.setattr(deploy, "_get_cw_client", lambda *args: _CloudWatch(["INSUFFICIENT_DATA"]))

    assert deploy.run(_args()) == 2
    assert lam.configuration_updates == []


def test_monitor_failure_restores_stable_alias(monkeypatch):
    lam = _Lambda(alias={"FunctionVersion": "1"})
    monkeypatch.setattr(deploy, "_get_lambda_client", lambda *args: lam)
    monkeypatch.setattr(
        deploy,
        "_get_cw_client",
        lambda *args: _CloudWatch(["OK", RuntimeError("monitor unavailable")]),
    )
    monkeypatch.setattr(deploy.time, "sleep", lambda seconds: None)

    assert deploy.run(_args()) == 1
    assert lam.configuration_updates
    assert [call["FunctionVersion"] for call in lam.alias_updates] == ["2", "1"]
    assert lam.alias_updates[-1]["RoutingConfig"] == {"AdditionalVersionWeights": {}}
