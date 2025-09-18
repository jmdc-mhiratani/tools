import os
import shutil

def delete_files_in_folder(folder_name):
    # 現在のディレクトリを取得
    current_dir = os.getcwd()
    folder_path = os.path.join(current_dir, folder_name)
    
    # フォルダが存在するか確認
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # フォルダ内のすべてのファイルとサブフォルダを削除
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # ファイルまたはシンボリックリンクを削除
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # サブフォルダを再帰的に削除
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"Folder '{folder_name}' does not exist.")

# 実行
delete_files_in_folder("Input")
delete_files_in_folder("Output")
