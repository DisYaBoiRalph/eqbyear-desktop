fn main() {
    // Tauri's default manifest is DPI-unaware, so Windows would bitmap-stretch the window.
    #[cfg(windows)]
    let windows_attributes = tauri_build::WindowsAttributes::new().app_manifest(
        r#"<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0" xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
  <asmv3:application>
    <asmv3:windowsSettings xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">
      <dpiAware>true/pm</dpiAware>
    </asmv3:windowsSettings>
    <asmv3:windowsSettings xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">
      <dpiAwareness>PerMonitorV2</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>
"#,
    );

    #[cfg(windows)]
    let attributes = tauri_build::Attributes::new().windows_attributes(windows_attributes);
    #[cfg(not(windows))]
    let attributes = tauri_build::Attributes::new();

    tauri_build::try_build(attributes).expect("failed to run tauri-build");
}
