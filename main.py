from modules.arguments_parser.parser import args


def debug_arg_test():
    for flag_name, value in args.items():
        print(flag_name, ":")

        if isinstance(value, list):
            for element in value:
                print('\t', element)
        else:
            print("\t", value)


if __name__ == "__main__":
    debug_arg_test()
