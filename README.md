# AI Motivation Letter Generator

Een krachtige Python applicatie die automatisch gepersonaliseerde motivatiebrieven genereert op basis van job descriptions van URLs, gebruikmakend van verschillende AI backends.

## 🎯 Features

### 🤖 **Multi-LLM Backend Support**

- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo, GPT-4o-mini
- **Ollama**: Lokale modellen (Llama3.1, Mistral, Phi4, QWQ)
- **Groq**: Snelle inferentie met Llama3, Mixtral, Gemma modellen

### 🌐 **Automatische Job Scraping**

- Extractie van job descriptions van URLs
- Intelligente herkenning van bedrijfsnaam, functietitel, en vereisten
- Support voor de meeste job sites (LinkedIn, Indeed, bedrijfswebsites)

### 📝 **Gepersonaliseerde Brief Generatie**

- Op maat gemaakte motivatiebrieven gebaseerd op uw CV en job description
- Meertalige support (Nederlands en Engels)
- Contextbewuste matching van skills en ervaring

### 👤 **Resume Management**

- Geïntegreerde CV editor voor persoonlijke gegevens
- Automatische personalisatie op basis van CV data
- Skills en ervaring management

### 📊 **Professionele UI/UX**

- Tabbed interface voor verschillende functies
- Real-time status updates en progress indicators
- History tracking van gegenereerde brieven
- Clipboard integratie en file management

## 🚀 Installation

### Vereisten

- Python 3.8 of hoger
- Internet verbinding voor AI backends en job scraping

### Stap 1: Clone Repository

```bash
git clone https://github.com/yourusername/motivation-letter-generator.git
cd motivation-letter-generator
```

### Stap 2: Installeer Dependencies

```bash
pip install -r requirements.txt
```

### Stap 3: Run de Applicatie

```bash
python motivation_letter_generator.py
```

## 📋 Dependencies

```txt
# Core dependencies
tkinter>=8.6.0
requests>=2.31.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
plyer>=2.1.0

# LLM Backend dependencies (optioneel)
openai>=1.0.0
ollama>=0.1.0
groq>=0.4.0

# Additional utilities
python-dateutil>=2.8.0
```

## ⚙️ Configuration

### 1. AI Backend Setup

#### OpenAI

1. Ga naar [OpenAI API](https://platform.openai.com/api-keys)
2. Genereer een API key
3. Voer de key in bij Configuration > OpenAI API Key

#### Groq

1. Ga naar [Groq Console](https://console.groq.com/)
2. Genereer een API key
3. Voer de key in bij Configuration > Groq API Key

#### Ollama (Lokaal)

1. Installeer [Ollama](https://ollama.ai/)
2. Start Ollama service: `ollama serve`
3. Download een model: `ollama pull llama3.1`
4. De applicatie detecteert automatisch lokale Ollama installatie

### 2. Resume Data

1. Ga naar de **Resume** tab
2. Vul uw persoonlijke gegevens in
3. Voeg uw professionele samenvatting toe
4. Lijst uw technische skills op
5. Klik **Save Resume**

## 🎯 Gebruik

### Stap 1: Configureer Backend

1. Open de **Configuration** tab
2. Selecteer uw gewenste AI backend (OpenAI/Ollama/Groq)
3. Voer de benodigde API credentials in
4. Test de verbinding
5. Sla de configuratie op

### Stap 2: Job URL Invoeren

1. Ga naar de **Letter Generator** tab
2. Plak de URL van de job posting
3. Klik **🔍 Scrape Job**
4. Controleer de geëxtraheerde job informatie

### Stap 3: Genereer Motivatiebrief

1. Selecteer gewenste taal (Engels/Nederlands)
2. Klik **✨ Generate Letter**
3. Wacht op AI processing
4. Review de gegenereerde brief

### Stap 4: Save & Export

1. Klik **📋 Copy** om naar clipboard te kopiëren
2. Klik **💾 Save** om op te slaan
3. Bekijk opgeslagen brieven in **History** tab

## 📁 File Structure

```
motivation-letter-generator/
├── motivation_letter_generator.py    # Hoofdapplicatie
├── requirements.txt                  # Dependencies
├── README.md                        # Dit bestand
└── ~/.motivation-gen/               # User data directory
    ├── config.json                  # Configuratie
    ├── resume.json                  # CV data
    ├── letters/                     # Opgeslagen brieven
    └── app.log                      # Applicatie logs
```

## 🎨 Screenshots

### Main Interface

![Generator Tab](screenshots
![Config Tab](screenshots/config& Best Practices

### Job URL's

- **Werkt goed**: DirectJobs, bedrijfswebsites, openbare job boards
- **Beperkt**: LinkedIn (inlog vereist), Indeed (anti-bot measures)
- **Tip**: Kopieer job description handmatig als URL scraping faalt

### AI Backend Keuze

- **OpenAI**: Beste kwaliteit, kost credits
- **Groq**: Snelle respons, gratis tier beschikbaar  
- **Ollama**: Volledig lokaal, gratis, langzamer

### Motivatiebrief Kwaliteit

- Zorg voor complete CV data in Resume tab
- Gebruik specifieke functietitels en bedrijfsnamen
- Review en edit gegenereerde brieven voor personalisatie

## 🔧 Troubleshooting

### Veel Voorkomende Problemen

#### "Backend Error: API key required"

- Controleer of API key correct is ingevoerd
- Test verbinding in Configuration tab

#### "Scraping Failed"

- Controleer internet verbinding
- Probeer een andere job URL
- Kopieer job description handmatig

#### "Model not found" (Ollama)

- Start Ollama service: `ollama serve`
- Download model: `ollama pull llama3.1`
- Controleer Ollama URL in configuratie

#### Applicatie start niet

```bash
# Controleer Python versie
python --version

# Installeer dependencies opnieuw
pip install -r requirements.txt

# Run met debug output
python motivation_letter_generator.py
```

## 🤝 Contributing

Contributions zijn welkom!

### Development Setup

```bash
git clone https://github.com/yourusername/motivation-letter-generator.git
cd motivation-letter-generator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Pull Request Process

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/amazing-feature`)
3. Commit uw changes (`git commit -m 'Add amazing feature'`)
4. Push naar branch (`git push origin feature/amazing-feature`)
5. Open een Pull Request

## 📄 License

Dit project is gelicenseerd onder de MIT License - zie het [LICENSE](LICENSE) bestand voor details.

## 🙏 Acknowledgments

- **Beautiful Soup** voor web scraping capabilities
- **OpenAI**, **Groq**, en **Ollama** voor AI inference
- **Tkinter** voor GUI framework
- **Plyer** voor cross-platform notifications

## 📞 Support

### Bug Reports

Open een [GitHub Issue](https://github.com/yourusername/motivation-letter-generator/issues) met:

- Beschrijving van het probleem
- Stappen om te reproduceren
- Verwacht vs. actueel gedrag
- Log output (indien beschikbaar)

### Feature Requests

Suggesties voor nieuwe features zijn welkom via GitHub Issues.

### Contact

- **Author**: Yilmaz Mustafa
- **Email**: [ymus@tuta.io]
- **GitHub**: [@codesapienbe]

---

**Built with ❤️ for job seekers everywhere**

*Gemaakt in België 🇧🇪*
