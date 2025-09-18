import fitz  # PyMuPDF
import os

def pdf_to_images_with_resizing(input_folder, scale=2.0):
    """
    PDFを画像化し、サイズを調整する。
    
    Parameters:
        input_folder (str): PDFファイルが格納されているフォルダ
        scale (float): 画像スケール。1.0で元サイズ、2.0で2倍。
    """
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith('.pdf'):
            file_path = os.path.join(input_folder, file_name)
            try:
                doc = fitz.open(file_path)  # PDFを開く
                base_name = os.path.splitext(file_name)[0]
                output_folder = os.path.join(input_folder, "../Output")
                os.makedirs(output_folder, exist_ok=True)

                for page_number in range(len(doc)):
                    page = doc[page_number]

                    # サイズを調整するためのスケール設定
                    zoom_matrix = fitz.Matrix(scale, scale)  # 横と縦のスケールを設定
                    pix = page.get_pixmap(matrix=zoom_matrix)  # サイズ調整された画像を生成

                    output_file = os.path.join(output_folder, f"{base_name}_{page_number + 1}.png")
                    pix.save(output_file)
                    print(f"Saved: {output_file}")
            except Exception as e:
                print(f"Error processing {file_name}: {e}")

# 実行
input_folder = './Input'
scale_factor = 1.5  # 画像のスケールを1.5倍に設定
pdf_to_images_with_resizing(input_folder, scale=scale_factor)
