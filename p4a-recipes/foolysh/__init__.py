"""
Recipe for foolysh.
"""

from multiprocessing import cpu_count

from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class FoolyshRecipe(CppCompiledComponentsPythonRecipe):
    version = 'p4a'
    url = 'https://github.com/tcdude/foolysh/archive/{version}.zip'
    site_packages_name = 'foolysh'

    depends = ['python3', 'numpy', 'pysdl2', 'Pillow', 'plyer', 'setuptools']

    def build_compiled_components(self, arch):
        self.setup_extra_args = ['-j', str(cpu_count())]
        super(FoolyshRecipe, self).build_compiled_components(arch)
        self.setup_extra_args = []

    def rebuild_compiled_components(self, arch, env):
        self.setup_extra_args = ['-j', str(cpu_count())]
        super(FoolyshRecipe, self).rebuild_compiled_components(arch, env)
        self.setup_extra_args = []

recipe = FoolyshRecipe()
