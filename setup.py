"""Include the checkout's canonical YAML resources in built packages."""
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


CONFIG_FILES = (
    "default.yaml",
    "venues.yaml",
    "leagues/ratings.yaml",
    "leagues/soccer.yaml",
    "leagues/team_aliases.yaml",
)


class BuildWithConfig(build_py):
    def run(self):
        super().run()
        resource_root = Path(self.build_lib) / "sqp" / "_config_resources"
        for name in CONFIG_FILES:
            target = resource_root / name
            self.mkpath(str(target.parent))
            self.copy_file(str(Path("configs") / name), str(target))


setup(cmdclass={"build_py": BuildWithConfig})
