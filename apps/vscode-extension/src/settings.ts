interface ConfigurationInspection<T> {
    globalValue?: T;
    workspaceValue?: T;
    workspaceFolderValue?: T;
    globalLanguageValue?: T;
    workspaceLanguageValue?: T;
    workspaceFolderLanguageValue?: T;
}

export interface ConfigurationReader {
    get<T>(section: string, defaultValue: T): T;
    inspect<T>(section: string): ConfigurationInspection<T> | undefined;
}

function hasExplicitValue<T>(inspection: ConfigurationInspection<T> | undefined): boolean {
    return inspection !== undefined && [
        inspection.globalValue,
        inspection.workspaceValue,
        inspection.workspaceFolderValue,
        inspection.globalLanguageValue,
        inspection.workspaceLanguageValue,
        inspection.workspaceFolderLanguageValue
    ].some(value => value !== undefined);
}

/**
 * Prefer an explicitly configured EOLkits setting, then its legacy Rupture
 * equivalent. Manifest defaults never hide an explicit pre-rebrand value.
 */
export function resolveSetting<T>(
    current: ConfigurationReader,
    legacy: ConfigurationReader,
    section: string,
    defaultValue: T
): T {
    if (hasExplicitValue(current.inspect<T>(section))) {
        return current.get<T>(section, defaultValue);
    }
    if (hasExplicitValue(legacy.inspect<T>(section))) {
        return legacy.get<T>(section, defaultValue);
    }
    return current.get<T>(section, defaultValue);
}
