# seeder.py
from pathlib import Path
import json
from db import engine, SessionLocal
from models import Base, CourseA, CourseB, CourseC, CourseD, Coursework

# создаём таблицы
Base.metadata.create_all(bind=engine)

# путь до папки с subject-файлами
SUBJECTS_DIR = Path(__file__).parent / "subjects"

# сопоставление имени файла -> отображаемое имя курса и модели
COURSE_MAP = {
    "course_a": ("Курс A", CourseA),
    "course_b": ("Курс B", CourseB),
    "course_c": ("Курс C", CourseC),
    "course_d": ("Курс D", CourseD),
}

def read_subjects_from_file(path: Path):
    """Читает файл, возвращает список subject-строк, убирает пустые и дубликаты."""
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name:
                continue
            if name not in items:
                items.append(name)
    return items

def seed():
    s = SessionLocal()
    try:
        for fname, (course_name, model) in COURSE_MAP.items():
            fpath = SUBJECTS_DIR / f"{fname}.txt"
            subjects = read_subjects_from_file(fpath)
            if not subjects:
                print(f"[seeder] {fpath} пуст или отсутствует — пропускаю.")
                continue
            for subj in subjects:
                # проверяем, нет ли уже такого предмета
                existing = s.query(model).filter_by(subject=subj).one_or_none()
                if existing is None:
                    obj = model(subject=subj, has_note=False, pdf_filename=None)
                    s.add(obj)
                    print(f"[seeder] Добавлен: {course_name} -> {subj}")
                else:
                    # если есть — не трогаем (идем дальше)
                    print(f"[seeder] Пропущен (уже есть): {course_name} -> {subj}")
        s.commit()
        print("[seeder] Готово.")
    finally:
        s.close()

if __name__ == "__main__":
    seed()
