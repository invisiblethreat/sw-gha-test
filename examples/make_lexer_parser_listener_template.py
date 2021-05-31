

LISTENER_ENTER_TEMPLATE = """
    # Enter a parse tree produced by PathGrammarParser#{parser}.
    def enter{camal}(self, ctx:PathGrammarParser.{camal}Context):
        self.add_context("{context_name}", ctx)
        pass"""

LISTENER_EXIT_TEMPLATE = """
    # Exit a parse tree produced by PathGrammarParser#{parser}.
    def exit{camal}(self, ctx:PathGrammarParser.{camal}Context):
        pass"""

ANALYZER_CLASS_TEMPLATE = """
    @property
    def is_{context_name}(self):
        \"\"\"Get {context_name}\"\"\"
    
        if '{context_name}' in self.contexts:
            return True
        return False"""


def format_lexer_name(name, directory=False):
    if name.startswith('.'):
        name = "dot_%s" % (name[1:])
    new_name = name.replace('-', '_').replace('.', '_').upper()
    if new_name.endswith('_'):
        new_name = "".join(new_name[0:-1])
    if directory:
        new_name = "%s_DIR" % (new_name)
    return new_name

def format_parser_name(name, directory=False):
    if name.startswith('.'):
        name = "dot_%s" % (name[1:])
    new_name = name.replace('-', '_').replace('.', '_').lower()
    if new_name.endswith('_'):
        new_name = "".join(new_name[0:-1])
    if directory:
        new_name = "%s_dir" % (new_name)
    return new_name

def format_camal_name(name, directory=False):
    parser_name = format_parser_name(name, directory=directory)
    first_char = parser_name[0].upper()
    camal_name = first_char + parser_name[1:]
    return camal_name

def make_lexer_entry(name, directory=False):
    column_size = 24
    fill_size = max(1, column_size - len(name))
    
    format_name = format_lexer_name(name, directory=directory)
    if directory:
        entry = "%s %s : '%s' SEPARATOR ;" % (format_name, " " * fill_size, name)
    else:
        entry = "%s %s : '%s' ;" % (format_name, " " * fill_size, name)
    return entry

def make_parser_entry(name, directory=False):
    column_size = 20
    fill_size = max(1, column_size - len(name))

    format_name = format_parser_name(name, directory=directory)
    entry = "%s %s : %s ;" % (format_name, " " * fill_size, format_lexer_name(name, directory=directory))
    return entry

def make_listener_enter(name, directory=False):
    parser = format_parser_name(name, directory=directory)
    camal = format_camal_name(name, directory=directory)
    if not parser.endswith('_dir'):
        # Will turn drone_yaml into drone_yaml_file
        context_name = "%s_file" % (parser)
    else:
        context_name = parser
    format_template = LISTENER_ENTER_TEMPLATE.format(parser=parser, camal=camal, context_name=context_name)
    return format_template

def make_listener_exit(name, directory=False):
    parser = format_parser_name(name, directory=directory)
    camal = format_camal_name(name, directory=directory)
    format_template = LISTENER_EXIT_TEMPLATE.format(parser=parser, camal=camal)
    return format_template

def make_analyzer_class_template(name, directory=False):
    parser_name = format_parser_name(name, directory=directory)
    if not parser_name.endswith('_dir'):
        # Will turn drone_yaml into drone_yaml_file
        context_name = "%s_file" % (parser_name)
        # base_name = parser_name
    else:
        context_name = parser_name
        # Will turn 'doc_dir' into 'doc'
        # base_name = parser_name[:-4]
    # format_template = ANALYZER_CLASS_TEMPLATE.format(base_name=base_name, context_name=context_name)
    format_template = ANALYZER_CLASS_TEMPLATE.format(context_name=context_name)
    return format_template

def main():
    """main"""

    # name = "root"
    directory = True

    names = [
        'ansible',
    ]

    print("=" * 80)
    print("= Add to 'PathGrammar.g4'")
    print("=" * 80)
    
    print("====== Parser ======")
    for name in names:
        print(make_parser_entry(name, directory=directory))

    print("====== Lexer =======")
    for name in names:
        print(make_lexer_entry(name, directory=directory))

    print("")
    print("=" * 80)
    print("= Add to 'AnalyzerPathGrammarListener.py'")
    print("=" * 80)
    for name in names:
        print(make_listener_enter(name, directory=directory))
        if directory:
            print(make_listener_exit(name, directory=directory))

    print("")
    print("=" * 80)
    print("= Add to 'context.py'")
    print("=" * 80)
    for name in names:
        print(make_analyzer_class_template(name, directory=directory))


if __name__ == "__main__":
    main()
