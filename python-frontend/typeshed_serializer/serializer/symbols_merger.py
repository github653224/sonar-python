from typing import Dict, Set, List

from serializer.symbols import ModuleSymbol, MergedFunctionSymbol, MergedClassSymbol, MergedOverloadedFunctionSymbol, \
    MergedModuleSymbol
from serializer import typeshed_serializer as ts

SUPPORTED_PYTHON_VERSIONS = ((2, 7), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9))


def build_multiple_python_version() -> Dict[str, Dict[str, ModuleSymbol]]:
    model_by_version: Dict[str, Dict[str, ModuleSymbol]] = {}
    for major, minor in SUPPORTED_PYTHON_VERSIONS:
        build_result = ts.walk_typeshed_stdlib(ts.get_options((major, minor)))
        modules = {}
        for file in build_result.files:
            ms = ModuleSymbol(build_result.files.get(file))
            modules[ms.fullname] = ms
        model_by_version[f"{major}{minor}"] = modules
    return model_by_version


def merge_multiple_python_versions():
    model_by_version = build_multiple_python_version()
    all_python_modules: Set[str] = set()
    for version in model_by_version:
        model = model_by_version[version]
        for module_fqn in model:
            mod: ModuleSymbol = model[module_fqn]
            all_python_modules.add(mod.fullname)
    merged_modules = merge_modules(all_python_modules, model_by_version)
    return merged_modules


def merge_modules(all_python_modules: Set[str], model_by_version: Dict[str, Dict[str, ModuleSymbol]]):
    merged_modules: Dict[str, MergedModuleSymbol] = {}
    for python_mod in all_python_modules:
        handled_classes: Dict[str, List[MergedClassSymbol]] = {}
        handled_funcs: Dict[str, List[MergedFunctionSymbol]] = {}
        handled_overloaded_functions: Dict[str, List[MergedOverloadedFunctionSymbol]] = {}
        merged_modules[python_mod] = MergedModuleSymbol(python_mod, handled_classes,
                                                        handled_funcs, handled_overloaded_functions)
        for version in model_by_version:
            model = model_by_version[version]
            # get current module
            if python_mod not in model:
                continue
            current_module = model[python_mod]
            merge_classes(current_module, handled_classes, version)
            merge_functions(current_module, handled_funcs, version)
            merge_overloaded_functions(current_module, handled_overloaded_functions, version)
    return merged_modules


def merge_classes(current_module, handled_classes, version):
    for mod_class in current_module.classes:
        if mod_class.fullname not in handled_classes:
            functions = {}
            overloaded_functions = {}
            merge_functions(mod_class, functions, version)
            merge_overloaded_functions(mod_class, overloaded_functions, version)
            handled_classes[mod_class.fullname] = [MergedClassSymbol(mod_class, functions,
                                                                     overloaded_functions, [version])]
        else:
            # merge
            compared = handled_classes[mod_class.fullname]
            for elem in compared:
                if elem.class_symbol == mod_class:
                    functions = elem.methods
                    overloaded_functions = elem.overloaded_methods
                    merge_functions(mod_class, functions, version)
                    merge_overloaded_functions(mod_class, overloaded_functions, version)
                    elem.valid_for.append(version)
                    break
            else:
                functions = {}
                overloaded_functions = {}
                merge_functions(mod_class, functions, version)
                merge_overloaded_functions(mod_class, overloaded_functions, version)
                compared.append(MergedClassSymbol(mod_class, functions, overloaded_functions, [version]))


def merge_overloaded_functions(module_or_class, handled_overloaded_funcs, version):
    functions = (module_or_class.overloaded_functions
                 if isinstance(module_or_class, ModuleSymbol) else module_or_class.overloaded_methods)
    for func in functions:
        if func.fullname not in handled_overloaded_funcs:
            # doesn't exist: we add it
            handled_overloaded_funcs[func.fullname] = [MergedOverloadedFunctionSymbol(func, [version])]
        else:
            compared = handled_overloaded_funcs[func.fullname]
            for elem in compared:
                if elem.overloaded_function_symbol == func:
                    elem.valid_for.append(version)
                    break
            else:
                # no equivalent yet in the variations: add a new one
                handled_overloaded_funcs[func.fullname].append(MergedOverloadedFunctionSymbol(func, [version]))


def merge_functions(module_or_class, handled_funcs, version):
    functions = module_or_class.functions if isinstance(module_or_class, ModuleSymbol) else module_or_class.methods
    for func in functions:
        if func.fullname not in handled_funcs:
            # doesn't exist: we add it
            handled_funcs[func.fullname] = [MergedFunctionSymbol(func, [version])]
        else:
            compared = handled_funcs[func.fullname]
            for elem in compared:
                if elem.function_symbol == func:
                    elem.valid_for.append(version)
                    break
            else:
                # no equivalent yet in the variations: add a new one
                handled_funcs[func.fullname].append(MergedFunctionSymbol(func, [version]))