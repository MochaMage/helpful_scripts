import os
import sys
import shutil
import timeit
from re import search
from PIL import Image
from multiprocessing import Pool

from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from reportlab.lib.pagesizes import letter


def images_to_pdf(image_files, parent_directory, pdf_filename):
    def parse_filename(f):
        regex = search("^(score_)?(\d*).*\.(\w+)$", f)
        num = regex.group(2)
        extension = regex.group(3)
        return num, extension

    def filename_to_int(f):
        num, _ = parse_filename(f)[0]
        return 0 if not num else int(num)

    def get_drawing_and_dimensions(image_filename):
        _, file_extension = parse_filename(image_filename)
        if file_extension == "svg":
            drawing = svg2rlg(image_filename)
            return drawing, drawing.width, drawing.height
        else:
            drawing = Image.open(image_filename)
            return drawing, drawing.size[0], drawing.size[1]

    try:
        print(f"{pdf_filename} : Processing sheets.")

        image_files.sort(key=filename_to_int)
        if (image_files[0] == ".DS_Store"):
            image_files.pop(0)

        _, reference_width, reference_height = get_drawing_and_dimensions(
            f"{parent_directory}/{pdf_filename}/{image_files[0]}")
        pdf_full_path = f"{parent_directory}/{pdf_filename}.pdf"
        pdf = canvas.Canvas(pdf_full_path, pagesize=(
            reference_width, reference_height))

        for f in image_files:
            num, file_extension = parse_filename(f)
            image_filename = f"{parent_directory}/{pdf_filename}/{f}"

            if file_extension == "svg":
                drawing, _, _ = get_drawing_and_dimensions(image_filename)
                renderPDF.draw(drawing, pdf, 0, 0)
            else:
                drawing, img_width, img_height = get_drawing_and_dimensions(
                    image_filename)
                pdf.drawImage(image_filename, 0, 0, img_width, img_height)

            print(f"{pdf_filename} : Page {num} added to PDF.")
            pdf.showPage()
        pdf.save()
        print(f"Created PDF '{pdf_full_path}'")
        shutil.rmtree(f"{parent_directory}/{pdf_filename}", ignore_errors=True)
        print(f"{pdf_filename} - Removed image directory.")
    except Exception as e:
        print(f"{pdf_filename} : PDF generation failure: {e}")


if __name__ == "__main__":
    start = timeit.default_timer()
    pdf_count = 0
    total_files = 0
    pool = Pool()
    for root, dirs, files in os.walk(sys.argv[1]):
        if len(files) >= 1 and files[0] != ".DS_Store":
            regex = search("^(.*)/(.*)", root)
            directory = regex.group(1)
            filename = regex.group(2)

            pdf_count += 1
            total_files += len(files)

            pool.apply_async(images_to_pdf, args=(files, directory, filename))

    pool.close()
    pool.join()
    stop = timeit.default_timer()
    print(f"Time: {
          stop - start} seconds. Total PDFs: {pdf_count}. Total files: {total_files}")
