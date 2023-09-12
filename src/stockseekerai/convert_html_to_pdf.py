import glob
import os
import sys

import pdfkit
from dotenv import load_dotenv


def convert_html_to_pdf(html_path, pdf_save_path):
    try:
        config = pdfkit.configuration(wkhtmltopdf=os.getenv('path_wkhtmltopdf'))
        pdfkit.from_file(html_path, pdf_save_path, configuration=config)
    # It might throw an OSError. But the conversion is complete irrespective.
    except Exception as e:
        print(f"An error occurred: {e}")
        pass


def convert():
    # Load the environment variables from the .env file
    load_dotenv()
    # Get directory paths for all symbols as a list
    symbol_paths = [folder for folder in glob.glob(os.path.join(os.getenv('annual_reports_html_save_directory'), '*')) \
                    if os.path.isdir(folder)]
    for i, symbol_path in enumerate(symbol_paths):
        # Get symbol name
        symbol = symbol_path.split('/')[-1]
        # Get annual_report dates for the symbol. Directories are named by the annual_report date
        ar_dates_symbol_paths = [folder for folder in glob.glob(os.path.join(symbol_path, '*')) if
                                 os.path.isdir(folder)]
        # Iterate over each date and convert the html file to pdf file
        for ar_dates_symbol_path in ar_dates_symbol_paths:
            ar_paths = [file for file in glob.glob(os.path.join(ar_dates_symbol_path, '*')) if os.path.isfile(file)]
            # ar_paths should be a list of 1 element only i.e the report
            if len(ar_paths) < 1:
                print('No report found for: {} skipping...'.format(ar_dates_symbol_path))
                continue
            assert len(ar_paths) == 1
            date = ar_dates_symbol_path.split('/')[-1]
            pdf_save_dir = os.path.join(os.getenv('annual_reports_pdf_save_directory'), symbol, date)
            pdf_save_path = os.path.abspath(ar_paths[0]).replace('.htm', '.pdf')
            print('pdf_save_path: {}'.format(pdf_save_path))
            # If path exists, then the conversion has already happened before
            if os.path.exists(pdf_save_path):
                continue
            else:
                if not os.path.exists(pdf_save_dir):
                    os.makedirs(pdf_save_dir)
                print('htm path: {}'.format(os.path.abspath(ar_paths[0])))
                print('Saving: {}'.format(pdf_save_path))
                convert_html_to_pdf(os.path.abspath(ar_paths[0]), os.path.abspath(pdf_save_path))
        print('Completed: {}/{}'.format(i + 1, len(symbol_paths)))


if __name__ == '__main__':
    convert()
    sys.exit(0)
