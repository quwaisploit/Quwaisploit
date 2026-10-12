import sys
import readline
from core.loader import ModuleLoader
from core.banner import *
from core.program.version import *
from core.promptui import *

class QuwaisploitConsole:
    def __init__(self):
        self.loader = ModuleLoader()
        self.modules = {}
        self.current_module_name = None
        self.current_module_obj = None
        self.current_options = {}
        readline.parse_and_bind("tab: complete")

    def start(self):
        Banner()
        print(f"""      \033[1;31m+\033[1;37m=\033[1;34m[ \033[1;31m{Program.name} \033[1;37m{Program.version}
\033[1;31m+\033[1;37m=======\033[1;34m[ \033[1;37mCreated By \033[1;32m{Program.author}
      \033[1;31m+\033[1;37m=\033[1;34m[ \033[1;33m{Program.copyright}
        """)
        self.modules = self.loader.load_modules()

        total_modules = len(self.modules)
        category_counts = {}
        for mod_path in self.modules.keys():
            category = mod_path.split('/')[0]
            category_counts[category] = category_counts.get(category, 0) + 1

        if category_counts:
            print("  \033[1m[*] Modules Available\033[0m    :")
            for cat, count in sorted(category_counts.items()):
                print(f"      - \033[1;36m{cat.upper()}\033[0m: \033[1;31m{count} \033[1;37mmodules")

        while True:
            try:
                if self.current_module_name:
                    prompt = (
                        f"\001\033[4;31m\002quwaisploit\001\033[0m\002 "
                        f"(\001\033[1;34m\002{self.current_module_name}\001\033[0m\002) "
                        f"\001\033[1;37m\002>\001\033[0m\002 "
                        f"\001\033[1;32m\002"
                    )
                else:
                    prompt = (
                        f"\001\033[4;31m\002quwaisploit\001\033[0m\002 "
                        f"\001\033[1;37m\002>\001\033[0m\002 "
                        f"\001\033[1;32m\002"
                    )

                cmd_input = input(prompt).strip()
                sys.stdout.write("\033[0m")
                sys.stdout.flush()

                if not cmd_input:
                    continue

                parts = cmd_input.split(' ', 2)
                cmd = parts[0].lower()

                if cmd == 'exit':
                    print(f"{PromptUi.info} Exiting...\033[0m")
                    sys.exit(0)

                elif cmd == 'help':
                    self.show_help()

                elif cmd == 'show':
                    if len(parts) > 1 and parts[1].lower() == 'modules':
                        self.list_modules()
                    elif len(parts) > 1 and parts[1].lower() == 'options':
                        self.show_options()
                    else:
                        print(f"{PromptUi.info} Use 'show modules' or 'help'\033[0m")

                elif cmd == 'use':
                    if len(parts) > 1:
                        mod_target = parts[1]
                        if mod_target in self.modules:
                            self.current_module_name = mod_target
                            self.current_module_obj = self.modules[mod_target]
                            self.current_options = {
                                opt: details['default'] 
                                for opt, details in self.current_module_obj.info['options'].items()
                            }
                        else:
                            print(f"{PromptUi.error} Prompt doesnt found: {mod_target}\033[0m")
                    else:
                        print(f"{PromptUi.info}Use the following command: use exploit/example/sample_exploit\033[0m")

                elif cmd == 'back':
                    if self.current_module_name:
                        self.current_module_name = None
                        self.current_module_obj = None
                        self.current_options = {}
                    else:
                        print(f"{PromptUi.error} Not using any module. try use one.\033[0m")

                elif cmd == 'set':
                    if not self.current_module_obj:
                        print(f"{PromptUi.info} Please select any module first by using: 'use <module>'\033[0m")
                    elif len(parts) >= 3:
                        opt_name = parts[1].upper()
                        opt_value = parts[2]
                        if opt_name in self.current_options:
                            self.current_options[opt_name] = opt_value
                            print(f"\033[1;91m{opt_name} \033[1;34m=> \033[1;37m{opt_value}\033[0m")
                        else:
                            print(f"{PromptUi.error}[-] Option '{opt_name}' not in this modules.\033[0m")
                    else:
                        print(f"{PromptUi.error} Format wrong. use: set <OPTION> <VALUE>\033[0m")

                elif cmd == 'exploit' or cmd == 'run':
                    if not self.current_module_obj:
                        print(f"{PromptUi.error} Select Module first.\033[0m")
                    else:
                        missing = []
                        for opt, details in self.current_module_obj.info['options'].items():
                            if details['required'] and not str(self.current_options.get(opt, '')):
                                missing.append(opt)
                        
                        if missing:
                            print(f"{PromptUi.error} This option is missing: {', '.join(missing)}\033[0m")
                        else:
                            try:
                                self.current_module_obj.run(self.current_options)
                            except Exception as e:
                                print(f"{PromptUi.error} Error while running modules: {e}\033[0m")

                else:
                    print(f"{PromptUi.error} Invalid Syntax\033[0m")

            except KeyboardInterrupt:
                print("\n\033[1;93m[*] Use 'exit' to exit the program.\033[0m")
            except EOFError:
                print("\n\033[1;92m[*] Exiting....\033[0m")
                sys.exit(0)
            except Exception as e:
                print(f"\033[1;91m[-] Trouble happend: {e}\033[0m")

    def show_help(self):
        print("\n\033[1mCore Commands:\033[0m")
        print("  ==============")
        print("  \033[1mhelp\033[0m             Youre looking at me baby")
        print("  \033[1mshow modules\033[0m     Show all modules")
        print("  \033[1muse <module>\033[0m     use modules")
        print("  \033[1mexit\033[0m             exit from the program")
        print("\n\033[1mModule Commands (after 'use'):\033[0m")
        print("  ===============================")
        print("  \033[1mshow options\033[0m     Show the configuration")
        print("  \033[1mset <opt> <val>\033[0m   set value for the options")
        print("  \033[1mexploit / run\033[0m     run the selected modules")
        print("  \033[1mback\033[0m             exit from the modules\n")

    def list_modules(self):
        self.modules = self.loader.load_modules()
        
        print("\n\033[1m[*] Quwaisploit Modules\033[0m")
        print("\033[1;31m" + "=" * 95 + "\033[0m")
        print(f"\033[1m{'Module Path':<45} | {'Description'}\033[0m")
        print("\033[1;34m" + "-" * 95 + "\033[0m")
        for path, mod in sorted(self.modules.items()):
            desc = mod.info.get('description', 'N/A')
            print(f"\033[1;36m{path:<45}\033[0m | {desc}")
        print("\033[1;34m" + "=" * 95 + "\033[0m")
        print(f"\033[1mTotal Modul:\033[0m {len(self.modules)}\n")

    def show_options(self):
        if not self.current_module_obj:
            print("\033[1;91m[-] select modules using 'use <module>'.\033[0m")
            return

        info = self.current_module_obj.info
        print(f"\n\033[1mModule Name :\033[0m {info.get('name', 'N/A')}")
        print(f"\033[1mPath        :\033[0m \033[1;36m{self.current_module_name}\033[0m")
        print(f"\033[1mDescription :\033[0m {info.get('description', 'N/A')}\n")
        
        print(f"\033[1m{'Parameter':<12} | {'Current Value':<18} | {'Required':<14} | {'Description'}\033[0m")
        print("\033[1;34m" + "-" * 78 + "\033[0m")
        
        for opt, details in info['options'].items():
            val = self.current_options.get(opt, '')
            is_req = details.get('required', False)
            req_str = '\033[1;91myes\033[0m' if is_req else 'no (opsional)'
            desc = details.get('desc', '')
            print(f"\033[1m{opt:<12}\033[0m | {str(val):<18} | {req_str:<23} | {desc}")
        print("")
