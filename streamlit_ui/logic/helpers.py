from libs.enums import FileType

def get_file_type(file_name: str) -> FileType:
    ext = file_name.split(".")[-1]
    if ext == "pdf":
        return FileType.PDF
    elif ext == "txt":
        return FileType.TXT
    elif ext == "csv":
        return FileType.CSV
    elif ext == "json":
        return FileType.JSON
    elif ext == "docx":
        return FileType.DOCX
    else:
        raise ValueError(f"Unsupported file type: {ext}")
