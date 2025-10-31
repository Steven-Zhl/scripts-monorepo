"""用于将字典排序-自然排序相互转换的脚本"""

from argparse import ArgumentParser
from pathlib import Path
from typing import Optional
from os import rename
from shutil import copyfile

source_dir: Optional[Path] = None


def fix_dict_order(
    new_name_pattern: str = "Sorted_{index:0>3d}", save_in_other_dir: bool = True
):
    """
    修复误被字典序排序并Padding的文件名
    :param new_name_pattern: 新的文件名格式, 其中{index}会被替换为新的序号
    :param save_in_other_dir: 是否保存到其他目录
    """
    if source_dir is None or not source_dir.exists():
        print("目录不存在")
        return
    files = [file.name for file in source_dir.glob("*.*")]
    files.sort()  # 当前的文件顺序(字典序填充后的结果)
    file_count = len(files)
    dict_indexes = [index + 1 for index in range(file_count)]  # 原始文件的序号
    dict_indexes.sort(key=lambda x: str(x))  # 字典序的原始结果
    rename_map = {}
    for i in range(len(files)):
        ext = files[i].split(".")[-1]
        rename_map[files[i]] = (
            new_name_pattern.format(index=dict_indexes[i]) + "." + ext
        )
        print(f"{files[i]} => {rename_map[files[i]]}")

    confirm = input("确认重命名? (Y/n): ")
    if confirm == "n":
        print("取消重命名")
        return
    if save_in_other_dir:
        target_dir = source_dir.parent / (source_dir.name + "_fixed")
        target_dir.mkdir(exist_ok=True)
        for old_name, new_name in rename_map.items():
            old_path = source_dir / old_name
            new_path = target_dir / new_name
            copyfile(old_path, new_path)
    else:
        target_dir = source_dir
        for old_name, new_name in rename_map.items():
            old_path = source_dir / old_name
            new_path = target_dir / new_name
            rename(old_path, new_path)
    print("重命名完成")


if __name__ == "__main__":
    parser = ArgumentParser(description="修复误被字典序排序并Padding的文件名")
    parser.add_argument(
        "-S",
        "--source_dir",
        type=str,
        required=True,
        help="源文件目录",
    )
    parser.add_argument(
        "-P",
        "--new_name_pattern",
        type=str,
        default="Sorted_{index:0>3d}",
        help="新的文件名格式, 其中{index}会被替换为新的序号, 默认: Sorted_{index:0>3d}",
    )
    parser.add_argument(
        "-O",
        "--save_in_other_dir",
        action="store_true",
        help="是否保存到其他目录, 默认: False",
    )
    args = parser.parse_args()
    source_dir = Path(args.source_dir)
    fix_dict_order(args.new_name_pattern, args.save_in_other_dir)
