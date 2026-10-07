# Бродский в числах

Сбор текстов Иосифа Бродского, сборка EPUB и количественный анализ стиха и прозы
с интерактивным отчётом.

> Готовые интерактивные отчёты (откройте в браузере или включите GitHub Pages для папки `docs`):
> `docs/index.html` — «Бродский в числах», первая версия оформления;
> `docs/prosvet.html` — «Бродский на просвет»: то же и ещё раздел «Мир Бродского»
> (персонажи, места, транспорт, еда, напитки), новое оформление.
> В них есть цитаты из стихов в объёме, нужном для иллюстраций.
>
> Тексты Бродского защищены авторским правом. Кроме отчёта, в репозитории только код:
> корпус, книги, кэш страниц и собранные данные с цитатами создаются локально
> и перечислены в `.gitignore`.

## Канон для других авторов

`CANON.md` — общий подход к таким исследованиям (поэты и прозаики, любой язык): вопросы до начала,
сбор и очистка корпуса, измерения с порогами, самопроверка без ручной разметки, устройство отчёта
и список ловушек из этого проекта.

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
| 11. Отчёт, версия 1 | `analysis/patch_report3.py` (шаблон) + `analysis/build_report.py` | самодостаточный HTML |
| 12. Персонажи, места, транспорт, еда, напитки | `analysis/world.py` | `world.json` |
| 13. Отчёт, версия 2 «на просвет» | `analysis/patch_report4.py` (+ `report4.head.html`, `report4.chrome.js`, `report4.wmap.js`, `report4.world.js`, `report4.rgraph.js` — граф рифм) + `build_report.py out.html report4.template.html` | самодостаточный HTML |
| 14. Карта Венеции для раздела «Венеция» | `analysis/venice_map/build_map.py` (OpenStreetMap, ODbL; нужны `shapely`, `pyproj`, `numpy`) | `map-fragment.svg`, `points.json` лежат в репозитории; `block.py` вставляет карту в отчёт при `patch_report4.py` |
| 15. Живой портрет на первом экране и биография в «Хронологии» | `analysis/live_portrait/`: `portrait_block.py` (разметка), `portrait.js` (поведение), `sync_assets.py` (`bio` — подпись и биография из naprosvet-book; `final` — ролик из naprosvet/live/lp/final; `deploy` — ролик рядом со страницами); после `patch_report4.py` и `build_report.py` — `analysis/wrap_pages.py out2.html` (обёртки docs и сайта) | `portrait.mp4`, `portrait.webm` рядом с `docs/prosvet.html` и `brodsky/index.html`; постер встроен в страницу. Без `live_portrait/final/` `patch_report4.py` падает |

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
python world.py                                    # персонажи, места, словари вещей
python patch_report4.py && python build_report.py out2.html report4.template.html
```

## Методика

Определения мер, допущения и ограничения — в разделе «Методика» самого отчёта.
Кратко: леммы `pymorphy3` (без снятия омонимии), ударения `ruaccent` (отдельное окружение,
`transformers<5`), размер — по положению ударений и распределению межударных промежутков,
рифма — по звуковому окончанию от последнего ударного гласного, слоги — число гласных,
жанр определяется по форме строк, год — по авторской дате в последних строках текста.

Алгоритмы k-средних, t-SNE и SVD реализованы на numpy: в основном окружении scikit-learn,
gensim и umap несовместимы с numpy 2.x. Ручной разметки нет — все классификаторы автоматические.
