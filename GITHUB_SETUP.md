# 📤 Инструкция по публикации проекта на GitHub

## Шаг 1: Подготовка проекта

### 1.1. Создайте .gitignore

Создайте файл `.gitignore` в корне проекта:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/

# Логи
jarvis/logs/*.log
jarvis/logs/*.json
!jarvis/logs/.gitkeep

# Данные (не коммитим API ключи)
jarvis/data/elevenlabs_api_key.txt
jarvis/data/elevenlabs_voice_id.txt
jarvis/data/last_healthcheck.txt

# Временные файлы
*.tmp
*.temp
*.bak
*.swp
*~

# IDE
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# Сборка
build/
dist/
*.egg-info/
*.spec

# Windows
Thumbs.db
Desktop.ini
.DS_Store

# Установщики Python
python-*.exe
*.msi

# Модели Whisper (слишком большие)
*.pt
*.bin
models/

# Tools
tools/ffmpeg/
```

### 1.2. Создайте .gitkeep для пустых папок

```bash
# Создайте файлы для сохранения структуры папок
echo. > jarvis/logs/.gitkeep
echo. > jarvis/data/.gitkeep
```

### 1.3. Проверьте файлы

Убедитесь, что все важные файлы на месте:
- ✅ `README.md`
- ✅ `INSTALLER.bat`
- ✅ `requirements-core.txt`
- ✅ `requirements-dev.txt`
- ✅ Все Python файлы в `jarvis/`
- ✅ `run.bat`
- ✅ `scripts/`

## Шаг 2: Инициализация Git

### 2.1. Откройте терминал в папке проекта

```bash
cd D:\сс
```

### 2.2. Инициализируйте репозиторий

```bash
git init
```

### 2.3. Добавьте все файлы

```bash
git add .
```

### 2.4. Создайте первый коммит

```bash
git commit -m "Initial commit: Jarvis Voice Assistant v0.1.0"
```

## Шаг 3: Создание репозитория на GitHub

### 3.1. Войдите в GitHub

Откройте https://github.com и войдите в аккаунт

### 3.2. Создайте новый репозиторий

1. Нажмите **"+"** → **"New repository"**
2. Имя: `jarvis-voice-assistant` (или другое)
3. Описание: `Голосовой ассистент в стиле Jarvis из Iron Man`
4. Выберите **Public** или **Private**
5. **НЕ** создавайте README, .gitignore, license (уже есть)
6. Нажмите **"Create repository"**

### 3.3. Скопируйте URL репозитория

Например: `https://github.com/yourusername/jarvis-voice-assistant.git`

## Шаг 4: Подключение к GitHub

### 4.1. Добавьте remote

```bash
git remote add origin https://github.com/yourusername/jarvis-voice-assistant.git
```

### 4.2. Переименуйте ветку в main (если нужно)

```bash
git branch -M main
```

### 4.3. Отправьте код

```bash
git push -u origin main
```

## Шаг 5: Настройка репозитория

### 5.1. Добавьте описание

В настройках репозитория добавьте:
- **Topics**: `voice-assistant`, `jarvis`, `python`, `speech-recognition`, `tts`, `ai`
- **Website**: (если есть)
- **Description**: `Голосовой ассистент в стиле Jarvis из Iron Man для Windows`

### 5.2. Создайте Release

1. Перейдите в **Releases** → **"Create a new release"**
2. Tag: `v0.1.0` (важно: формат vX.Y.Z)
3. Title: `Jarvis Voice Assistant v0.1.0`
4. Описание:
   ```
   Первый релиз Jarvis Voice Assistant
   
   Возможности:
   - Распознавание речи (Google STT / Whisper)
   - Синтез речи (ElevenLabs / pyttsx3)
   - Semantic Router для умного понимания команд
   - Context-Aware команды
   - Асинхронный TTS
   - Система автоматических обновлений
   ```
5. Нажмите **"Publish release"**

**ВАЖНО:** После каждого релиза обновляйте версию в `jarvis/data/version.txt` и коммитьте изменения!

### 5.3. Настройка обновлений

Для автоматической проверки обновлений укажите репозиторий:

```bash
# Установите переменную окружения
set GITHUB_REPO=yourusername/jarvis-voice-assistant
```

Или пользователи могут указать при установке через INSTALLER.bat.

## Шаг 6: Обновление проекта

### 6.1. После изменений

```bash
# Добавить изменения
git add .

# Создать коммит
git commit -m "Описание изменений"

# Отправить на GitHub
git push
```

### 6.2. Создание новой ветки для фичи

```bash
# Создать ветку
git checkout -b feature/new-feature

# Внести изменения
# ...

# Коммит
git commit -m "Добавлена новая фича"

# Отправить ветку
git push -u origin feature/new-feature

# Создать Pull Request на GitHub
```

## Шаг 7: Дополнительные файлы (опционально)

### 7.1. LICENSE

Создайте файл `LICENSE` (MIT License):

```
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 7.2. CONTRIBUTING.md

Создайте файл `CONTRIBUTING.md` для разработчиков:

```markdown
# Вклад в проект

Спасибо за интерес к Jarvis Voice Assistant!

## Как внести вклад

1. Fork репозитория
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Внесите изменения
4. Коммит (`git commit -m 'Add amazing feature'`)
5. Push в ветку (`git push origin feature/amazing-feature`)
6. Создайте Pull Request

## Стандарты кода

- Используйте Python 3.11
- Следуйте PEP 8
- Добавляйте комментарии на русском
- Пишите логи на русском
```

## ✅ Чеклист перед публикацией

- [ ] Создан `.gitignore`
- [ ] Создан `README.md` с описанием
- [ ] Создан `INSTALLER.bat` для установки
- [ ] Все API ключи удалены из кода
- [ ] Все пароли удалены из кода
- [ ] Логи не содержат чувствительных данных
- [ ] Код проверен на ошибки
- [ ] README содержит инструкции по установке
- [ ] README содержит примеры использования
- [ ] Создан первый коммит
- [ ] Репозиторий создан на GitHub
- [ ] Код отправлен на GitHub

## 🎉 Готово!

Теперь ваш проект доступен на GitHub и другие люди могут:
- Клонировать репозиторий
- Использовать `INSTALLER.bat` для установки
- Вносить вклад в проект
- Создавать Issues

---

**Удачи с проектом! 🚀**

