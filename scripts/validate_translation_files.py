"""
Validate translation files using GNU gettext `msgfmt` command.
"""

import argparse
import os
import os.path
import subprocess
import sys
import textwrap

import i18n.validate


def get_translation_files(translation_directory):
    """
    List all translations '*.po' files in the specified directory.
    """
    po_files = []
    for root, _dirs, files in os.walk(translation_directory):
        for file_name in files:
            pofile_path = os.path.join(root, file_name)
            if file_name.endswith('.po') and '/en/LC_MESSAGES/' not in pofile_path:
                po_files.append(pofile_path)
    return po_files


def validate_translation_file(po_file):
    """
    Validate a translation file and return errors if any.

    This function combines both stderr and stdout output of the `msgfmt` in a
    single variable.
    """
    valid = True
    output = ""

    completed_process = subprocess.run(
        ['msgfmt', '-v', '--strict', '--check', po_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if completed_process.returncode != 0:
        valid = False

    msgfmt_stdout = completed_process.stdout.decode(encoding='utf-8', errors='replace')
    msgfmt_stderr = completed_process.stderr.decode(encoding='utf-8', errors='replace')
    output += f'{msgfmt_stdout}\n{msgfmt_stderr}\n'

    try:
      problems = i18n.validate.check_messages(po_file)
    except Exception as e:
      output += f'{e} {traceback.format_exc()}'
      valid = False
      problems = []
    if problems:
        valid = False

    id_filler = textwrap.TextWrapper(width=79, initial_indent="  msgid: ", subsequent_indent=" " * 9)
    tx_filler = textwrap.TextWrapper(width=79, initial_indent="  -----> ", subsequent_indent=" " * 9)
    for problem in problems:
        desc, msgid = problem[:2]
        output += f"{desc}\n{id_filler.fill(msgid)}\n"
        for translation in problem[2:]:
            output += f"{tx_filler.fill(translation)}\n"
        output += "\n"

    return {
        'valid': valid,
        'output': output,
        'failures': len(problems),
    }


def validate_translation_files(
    translations_dir='translations',
    all_files=False,
    full_report=False,
):
    """
    Run GNU gettext `msgfmt` and print errors to stderr.

    Returns integer OS Exit code:

      return 0 for valid translation.
      return 1 for invalid translations.
    """
    translations_valid = True
    invalid_lines = []
    total_failures = 0

    po_files = get_translation_files(translations_dir)

    for po_file in po_files:
        result = validate_translation_file(po_file)

        if not result['valid']:
            invalid_lines.append(f"INVALID: {po_file} | Failures: {result['failures']}")
            total_failures += result['failures']

            if full_report:
                invalid_lines.append(result['output'] + '\n' * 2)

            translations_valid = False
        elif all_files:
            print('VALID: ' + po_file)

            if full_report:
                print(result['output'], '\n' * 2)

    # Print validation errors in the bottom for easy reading
    print('\n'.join(invalid_lines), file=sys.stderr)

    if translations_valid:
        print('-----------------------------------------')
        print('SUCCESS: All translation files are valid.')
        print('-----------------------------------------')
        exit_code = 0
    else:
        print('------------------------------------------', file=sys.stderr)
        print(f'FAILURE: {total_failures} translations are invalid.', file=sys.stderr)
        print('------------------------------------------', file=sys.stderr)
        exit_code = 1

    return exit_code


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--filename', action='store', type=str, default=None, help='Filename to validate')
    parser.add_argument('-d','--dir', action='store', type=str, default='translations', help='Translations directory')
    parser.add_argument('-F', '--full-report', action='store_true', help='Print full output')
    parser.add_argument('-a', '--all', action='store_true', help='Include valid files in output')

    args = parser.parse_args()

    if args.filename:
        if not os.path.exists(args.filename):
            print(f"ERROR: {args.filename} does not exist.")
            sys.exit(1)

        result = validate_translation_file(args.filename)

        if not result['valid']:
            print(f"INVALID: {args.filename} | Failures: {result['failures']}")
            print(result['output'] + '\n' * 2)
            sys.exit(1)

        sys.exit(0)


    sys.exit(validate_translation_files(
        translations_dir=args.dir,
        all_files=args.all,
        full_report=args.full_report,
    ))


if __name__ == '__main__':
    main()  # pragma: no cover
