"""
Recipe for pyksolve.
"""

from multiprocessing import cpu_count

from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class PyksolveRecipe(CppCompiledComponentsPythonRecipe):
    version = 'v0.0.9'
    url = 'https://github.com/tcdude/py-klondike-solver/releases/download/' \
          '{version}/py-klondike-solver.zip'
    site_packages_name = 'pyksolve'

    depends = ['python3', 'setuptools']

    def build_compiled_components(self, arch):
        self.setup_extra_args = ['-j', str(cpu_count())]
        super(PyksolveRecipe, self).build_compiled_components(arch)
        self.setup_extra_args = []

    def rebuild_compiled_components(self, arch, env):
        self.setup_extra_args = ['-j', str(cpu_count())]
        super(PyksolveRecipe, self).rebuild_compiled_components(arch, env)
        self.setup_extra_args = []

recipe = PyksolveRecipe()
