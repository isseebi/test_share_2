import ast
import os
import re

def test_clean_architecture_boundaries():
    """
    Automated AST test verifying Clean Architecture import rules:
    - Domain layer must NOT import from Application, Infrastructure, or Interface layers.
    - Application layer must NOT import from Infrastructure or Interface layers.
    """
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
    assert os.path.exists(src_dir), "src directory not found"

    domain_pattern = re.compile(r"src[\\/]features[\\/][^\\/]+[\\/]domain")
    shared_domain_pattern = re.compile(r"src[\\/]shared[\\/]domain")
    app_pattern = re.compile(r"src[\\/]features[\\/][^\\/]+[\\/]application")

    errors = []

    for root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=filepath)
                except SyntaxError:
                    continue

            # Identify if file is in Domain or Application layer
            is_domain = bool(domain_pattern.search(filepath) or shared_domain_pattern.search(filepath))
            is_application = bool(app_pattern.search(filepath))

            for node in ast.walk(tree):
                imported_modules = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.append(node.module)

                for mod in imported_modules:
                    # Check Domain rule: No imports from application, infrastructure, or interface
                    if is_domain:
                        forbidden = ["application", "infrastructure", "interface"]
                        if any(f in mod.split(".") for f in forbidden):
                            errors.append(
                                f"Boundary violation in {filepath}: Domain layer imports '{mod}'"
                            )

                    # Check Application rule: No imports from infrastructure or interface
                    if is_application:
                        forbidden = ["infrastructure", "interface"]
                        if any(f in mod.split(".") for f in forbidden):
                            errors.append(
                                f"Boundary violation in {filepath}: Application layer imports '{mod}'"
                            )

    assert not errors, "Clean Architecture import boundary violations found:\n" + "\n".join(errors)
