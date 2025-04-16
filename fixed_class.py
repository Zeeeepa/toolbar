@dataclass
class EnhancedPluginManifest(PluginManifest):
    """Enhanced class representing a plugin manifest with additional fields."""
    # Required parameters must come first (inherited from PluginManifest)
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: Union[PluginType, ExtendedPluginType]
    main_class: str
    # Optional parameters with default values
    dependencies: List[PluginDependency] = None
    min_toolbar_version: str = "1.0.0"
    max_toolbar_version: str = "*"
    settings_schema: Dict[str, Any] = None
    # Additional fields specific to EnhancedPluginManifest
    icon_path: Optional[str] = None
    settings_ui_class: Optional[str] = None
    website: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    auto_start: bool = False
    update_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedPluginManifest':
        """Create an EnhancedPluginManifest from a dictionary."""
        # Convert plugin_type string to enum
        plugin_type_str = data.get("plugin_type", "other")
        try:
            plugin_type = ExtendedPluginType(plugin_type_str)
        except ValueError:
            try:
                plugin_type = PluginType(plugin_type_str)
            except ValueError:
                plugin_type = PluginType.OTHER
        
        # Convert dependencies list
        dependencies = []
        for dep in data.get("dependencies", []):
            dependencies.append(PluginDependency(
                plugin_id=dep.get("plugin_id"),
                version_requirement=dep.get("version_requirement", "*"),
                optional=dep.get("optional", False)
            ))
        
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            version=data.get("version"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=plugin_type,
            main_class=data.get("main_class"),
            dependencies=dependencies,
            min_toolbar_version=data.get("min_toolbar_version", "1.0.0"),
            max_toolbar_version=data.get("max_toolbar_version", "*"),
            settings_schema=data.get("settings_schema"),
            icon_path=data.get("icon_path"),
            settings_ui_class=data.get("settings_ui_class"),
            website=data.get("website"),
            repository=data.get("repository"),
            license=data.get("license"),
            tags=data.get("tags", []),
            required_permissions=data.get("required_permissions", []),
            auto_start=data.get("auto_start", False),
            update_url=data.get("update_url")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["plugin_type"] = self.plugin_type.value if self.plugin_type else "other"
        # Convert dependencies to dicts
        if self.dependencies:
            data["dependencies"] = [asdict(dep) for dep in self.dependencies]
        return data
