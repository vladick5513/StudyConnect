from typing import List, Optional

VALID_COUNTRIES = {
    "Россия", "Украина", "Беларусь", "Казахстан", "США", "Канада",
    "Великобритания", "Германия", "Франция", "Италия", "Испания",
    "Польша", "Китай", "Япония", "Южная Корея", "Австралия",
    "Бразилия", "Мексика", "Индия"
}

VALID_LANGUAGES = {
    "русский", "английский", "немецкий", "французский",
    "испанский", "китайский", "японский", "корейский",
    "итальянский", "португальский", "хинди", "арабский"
}

VALID_SUBJECTS = {
    "математика", "физика", "химия", "биология",
    "информатика", "программирование", "история",
    "география", "литература", "английский язык",
    "русский язык", "обществознание", "экономика",
    "философия", "психология", "музыка", "искусство",
    "право", "медицина", "маркетинг", "менеджмент"
}

MIN_AGE = 13
MAX_AGE = 80

def validate_country(country_name: str) -> Optional[str]:
    """Validates country name against the VALID_COUNTRIES set"""
    normalized_name = country_name.strip().title()
    return normalized_name if normalized_name in VALID_COUNTRIES else None

def validate_language(language_name: str) -> Optional[str]:
    """Validates language name against the VALID_LANGUAGES set"""
    normalized_name = language_name.lower().strip()
    return normalized_name if normalized_name in VALID_LANGUAGES else None

def validate_subjects(subjects: List[str]) -> bool:
    """Validates a list of subjects against the VALID_SUBJECTS set"""
    normalized_subjects = [subj.lower().strip() for subj in subjects]
    return all(subject in VALID_SUBJECTS for subject in normalized_subjects)
