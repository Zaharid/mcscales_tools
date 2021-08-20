class CheckError(Exception):
    pass


def check_is_valid_mcscales(pdf):
    if not pdf.path.is_dir():
        raise CheckError(
            f"{pdf.path} is not a valid LHAPDF grid. Path is not a directory."
        )
    if not pdf.infopath.is_file():
        raise CheckError(
            f"{pdf.path} is not a valid LHAPDF grid. Info file {pdf.infopath} is not a file."
        )
    if not pdf.member_path(0).is_file:
        raise CheckError(
            f"{pdf.path} is not a valid LHAPDF grid. Member 0 {pdf.member_path(0)} is not a file."
        )
    if not pdf.is_valid():
        raise CheckError(f"{pdf.path} is not a valid LHAPDF grid.")
    if "mcscales_processes" not in pdf.info:
        raise CheckError(f"{pdf.name} is not a MCscales grid. Key 'mcscales_processes' not found in the info file.")
