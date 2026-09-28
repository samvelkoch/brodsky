# Бродский в числах

Сбор текстов Иосифа Бродского, сборка EPUB и количественный анализ стиха и прозы
с интерактивным отчётом.

> Готовый интерактивный отчёт — `docs/index.html` (откройте в браузере или включите GitHub Pages
> для папки `docs`). В нём есть цитаты из стихов в объёме, нужном для иллюстраций.
>
> Тексты Бродского защищены авторским правом. Кроме отчёта, в репозитории только код:
> корпус, книги, кэш страниц и собранные данные с цитатами создаются локально
> и перечислены в `.gitignore`.

## Пайплайн

| Шаг | Скрипт | Результат (локально) |
|---|---|---|
| 1. Сбор текстов с iosif-brodskiy.ru | `scrape_brodsky.py` | `brodsky_all_texts.{txt,jsonl}`, журнал пропусков |
| 2. Дополнение из «Сочинений Иосифа Бродского» (7 т., EPUB) | `merge_sib.py` | `brodsky_combined.{txt,jsonl}` |
| 3. Сборка книг | `build_epub.py` | `brodsky_combined.epub` (оглавление раздел → период → текст) |
| 4. Венецианский сборник | `analysis/venice_score.py`, `analysis/build_venice.py` | `brodsky_venice.epub`, журнал отбора |
| 5. Разметка корпуса и леммы | `analysis/prepare.py` | `corpus.pkl` |
| 6. Статистика | `analysis/compute.py` | `stats.json` |
| 7. Данные для интерактива | `analysis/explorer.py` | `explorer.json` |
| 8. Ударения (отдельное окружение) | `analysis/export_lines.py`, `analysis/accent.py` | `accented.json` |
| 9. Стих: размер, рифма, звук, фраза | `analysis/verse.py` | `verse.json` |
| 10. Переломы стиля, группы, карта словаря | `analysis/style.py` | `style.json` |
| 11. Отчёт | `analysis/patch_report3.py` (шаблон) + `analysis/build_report.py` | самодостаточный HTML |

## Запуск

```bash
pip install -r requirements.txt
python scrape_brodsky.py
python merge_sib.py --sib-dir "<папка с EPUB семитомника>"
python build_epub.py --in brodsky_combined.jsonl --out brodsky_combined.epub

cd analysis
python prepare.py && python explorer.py          # explorer.py заодно пересчитывает compute.py
python export_lines.py
python -m venv .venv-accent && .venv-accent/bin/pip install -r requirements-accent.txt
.venv-accent/bin/python accent.py                # ~25 мин на CPU
python verse.py && python style.py
python patch_report3.py && python build_report.py out.html
```

## Методика

Определения мер, допущения и ограничения — в разделе «Методика» самого отчёта.
Кратко: леммы `pymorphy3` (без снятия омонимии), ударения `ruaccent` (отдельное окружение,
`transformers<5`), размер — по положению ударений и распределению межударных промежутков,
рифма — по звуковому окончанию от последнего ударного гласного, слоги — число гласных,
жанр определяется по форме строк, год — по авторской дате в последних строках текста.

Алгоритмы k-средних, t-SNE и SVD реализованы на numpy: в основном окружении scikit-learn,
gensim и umap несовместимы с numpy 2.x. Ручной разметки нет — все классификаторы автоматические.
