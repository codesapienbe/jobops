# JobOps - AI-Powered Job Application Assistant

A comprehensive Python application that automates the creation of personalized motivation letters and manages job application workflows using multiple AI backends.

## 🎯 Features

### 🤖 **Multi-LLM Backend Support**

- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo, GPT-4o-mini
- **Ollama**: Local models (Llama3.1, Mistral, Phi4, QWQ)
- **Groq**: Fast inference with Llama3, Mixtral, Gemma models

### 🌐 **Intelligent Job Scraping**

- Automatic extraction of job descriptions from URLs
- Smart recognition of company names, job titles, and requirements
- Support for most job sites (LinkedIn, Indeed, company websites)
- Fallback manual input for protected sites

### 📝 **Personalized Letter Generation**

- AI-powered motivation letters tailored to specific job postings
- Multi-language support (English and Dutch)
- Context-aware matching of skills and experience
- Professional tone and structure optimization

### 👤 **Comprehensive Resume Management**

- Integrated CV editor for personal information
- Skills and experience database
- Educational background tracking
- Certification and project portfolio

### 📊 **Professional User Interface**

- Modern tabbed interface for different workflows
- Real-time status updates and progress indicators
- Comprehensive history tracking and search
- Export capabilities and file management

### 🔧 **Advanced Automation**

- Batch processing for multiple applications
- Template customization and reuse
- Integration with clipboard and file systems
- Cross-platform compatibility (Windows, macOS, Linux)

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Internet connection for AI backends and job scraping
- 4GB RAM recommended for local AI models

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/jobops.git
cd jobops
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python jobops.py
```

## 📋 Dependencies

```txt
# Core Dependencies
tkinter>=8.6.0
requests>=2.31.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
plyer>=2.1.0

# AI Backend Dependencies (Optional)
openai>=1.0.0
ollama>=0.1.0
groq>=0.4.0

# Additional Utilities
python-dateutil>=2.8.0
numpy>=1.21.0
```

## ⚙️ Configuration

### 1. AI Backend Setup

#### OpenAI Configuration

1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Generate an API key
3. Enter the key in Configuration > OpenAI API Key
4. Select your preferred model (GPT-3.5-turbo recommended for cost efficiency)

#### Groq Configuration

1. Visit [Groq Console](https://console.groq.com/)
2. Create an account and generate an API key
3. Enter the key in Configuration > Groq API Key
4. Choose from available models (Llama3-8b-8192 recommended)

#### Ollama (Local) Configuration

1. Install [Ollama](https://ollama.ai/) on your system
2. Start Ollama service: `ollama serve`
3. Download a model: `ollama pull llama3.1`
4. JobOps will automatically detect local Ollama installation
5. Configure URL in settings (default: <http://localhost:11434>)

### 2. Resume Profile Setup

1. Navigate to the **Resume** tab
2. Fill in your personal information:
   - Full name and professional title
   - Years of experience
   - Location and contact details
3. Add your professional summary
4. List your technical skills (one per line)
5. Include work experience with descriptions
6. Add education and certifications
7. Click **Save Resume** to persist your data

## 🎯 Usage Guide

### Step 1: Configure Your AI Backend

1. Open the **Configuration** tab
2. Select your preferred AI backend from the dropdown
3. Enter the required API credentials
4. Test the connection using the "Test Connection" button
5. Save your configuration

### Step 2: Set Up Your Professional Profile

1. Switch to the **Resume** tab
2. Complete all sections of your professional profile
3. Focus on skills and experiences relevant to your target roles
4. Save your profile for future use

### Step 3: Process Job Applications

1. Go to the **Letter Generator** tab
2. Paste the URL of the job posting you're interested in
3. Click **🔍 Scrape Job** to extract job details
4. Review the extracted information for accuracy
5. Select your preferred language (English/Dutch)
6. Click **✨ Generate Letter** to create your motivation letter

### Step 4: Review and Customize

1. Review the AI-generated motivation letter
2. Make any necessary edits directly in the text area
3. Use **📋 Copy** to copy to clipboard
4. Use **💾 Save** to store the letter for future reference
5. Access saved letters in the **History** tab

### Advanced Features

#### Batch Processing

- Save multiple job URLs in a text file
- Use the batch processing feature to generate multiple letters
- Review and customize each letter individually

#### Template Management

- Create custom templates for different types of positions
- Reuse successful letter structures
- Maintain consistency across applications

#### Integration Workflow

- Export letters in multiple formats (PDF, DOCX, TXT)
- Integrate with email clients for direct sending
- Track application status and follow-ups

## 📁 Project Structure

```
jobops/
├── jobops.py                        # Main application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This documentation
├── LICENSE                         # MIT License
├── config/                         # Configuration files
│   ├── default_settings.json      # Default application settings
│   └── models_config.json         # AI model configurations
├── templates/                      # Letter templates
│   ├── technical_template.txt     # Technical position template
│   ├── management_template.txt    # Management position template
│   └── creative_template.txt      # Creative position template
├── assets/                         # Application assets
│   ├── icons/                     # Application icons
│   └── images/                    # UI images
├── docs/                          # Additional documentation
│   ├── API.md                     # API documentation
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   └── CHANGELOG.md               # Version history
└── ~/.jobops/                     # User data directory
    ├── config.json                # User configuration
    ├── resume.json                # User resume data
    ├── letters/                   # Saved motivation letters
    ├── templates/                 # Custom user templates
    └── logs/                      # Application logs
```

## 🎨 User Interface Overview

### Main Dashboard

- **Quick Actions**: One-click access to common tasks
- **Recent Applications**: Overview of recent job applications
- **Success Metrics**: Track your application success rate
- **Upcoming Deadlines**: Never miss an application deadline

### Letter Generator

- **URL Input**: Paste job posting URLs for automatic processing
- **Job Preview**: Review extracted job information before processing
- **AI Controls**: Select language, model, and generation parameters
- **Real-time Preview**: See your letter being generated in real-time

### Configuration Center

- **Backend Management**: Configure and test AI backends
- **Model Selection**: Choose optimal models for your use case
- **Performance Tuning**: Adjust generation parameters
- **Usage Analytics**: Monitor API usage and costs

### Resume Builder

- **Personal Information**: Comprehensive personal data management
- **Experience Timeline**: Visual representation of your career journey
- **Skills Matrix**: Organize and categorize your technical skills
- **Achievement Tracker**: Record and highlight your accomplishments

## 💡 Best Practices

### Job URL Processing

- **Preferred Sources**: Direct company websites, LinkedIn, Indeed
- **URL Requirements**: Ensure URLs are accessible without login
- **Fallback Strategy**: Copy job descriptions manually if scraping fails
- **Quality Check**: Always review scraped content for accuracy

### AI Backend Selection

- **OpenAI**: Best overall quality, costs per request
- **Groq**: Fast processing, good quality, free tier available
- **Ollama**: Completely local, free, requires more system resources

### Letter Optimization

- **Personalization**: Include specific company details and role requirements
- **Length Management**: Keep letters between 300-400 words
- **Tone Consistency**: Maintain professional yet engaging tone
- **Keyword Integration**: Include relevant keywords from job descriptions

### Resume Management

- **Regular Updates**: Keep your resume current with new skills and experiences
- **Targeted Content**: Customize resume focus for different types of roles
- **Achievement Focus**: Emphasize measurable accomplishments
- **Skill Relevance**: Prioritize skills most relevant to your target positions

## 🔧 Troubleshooting

### Common Issues and Solutions

#### "Backend Error: API key required"

- **Cause**: Missing or invalid API key configuration
- **Solution**:
  1. Check API key format and validity
  2. Ensure no extra spaces or characters
  3. Test connection using the built-in test feature
  4. Verify account status and credit balance

#### "Scraping Failed: Unable to extract job description"

- **Cause**: Protected website or anti-bot measures
- **Solution**:
  1. Try a different job URL from the same company
  2. Copy job description manually
  3. Check internet connection
  4. Verify URL is accessible in browser

#### "Model not found" (Ollama)

- **Cause**: Required model not downloaded locally
- **Solution**:

  ```bash
  # Start Ollama service
  ollama serve
  
  # Download required model
  ollama pull llama3.1
  
  # Verify model availability
  ollama list
  ```

#### Application Won't Start

- **Cause**: Missing dependencies or Python version issues
- **Solution**:

  ```bash
  # Check Python version (3.8+ required)
  python --version
  
  # Reinstall dependencies
  pip install -r requirements.txt --force-reinstall
  
  # Run with debug output
  python jobops.py --debug
  ```

#### Poor Letter Quality

- **Cause**: Incomplete resume data or inappropriate model selection
- **Solution**:
  1. Complete all resume sections thoroughly
  2. Try a different AI model or backend
  3. Adjust generation parameters
  4. Provide more specific job descriptions

### Performance Optimization

#### Speed Improvements

- Use Groq for fastest generation times
- Enable local caching for frequently used data
- Optimize resume data to reduce token usage
- Use smaller models for quick iterations

#### Quality Improvements

- Use GPT-4 for highest quality output
- Provide detailed job descriptions
- Maintain comprehensive resume data
- Review and refine generated content

#### Resource Management

- Monitor API usage and costs
- Use local models when possible
- Implement request caching
- Optimize prompt engineering

## 🤝 Contributing

We welcome contributions to JobOps! Here's how you can help:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/jobops.git
cd jobops

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start development server
python jobops.py --dev
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to your branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Add unit tests for new features
- Update documentation as needed
- Ensure cross-platform compatibility

### Issue Reporting

When reporting issues, please include:

- Operating system and Python version
- Complete error messages and stack traces
- Steps to reproduce the issue
- Expected vs. actual behavior
- Relevant configuration details

## 📄 License

JobOps is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 JobOps Contributors

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

## 🙏 Acknowledgments

### Technology Stack

- **Beautiful Soup** for intelligent web scraping capabilities
- **OpenAI**, **Groq**, and **Ollama** for powerful AI inference
- **Tkinter** for cross-platform GUI framework
- **Plyer** for system notifications and integrations

### Special Thanks

- Open source community for invaluable tools and libraries
- AI research community for advancing language model capabilities
- Beta testers who provided feedback and bug reports
- Contributors who helped improve documentation and features

## 📞 Support and Community

### Documentation

- **API Reference**: [docs/API.md](docs/API.md)
- **Contributing Guide**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Change Log**: [docs/CHANGELOG.md](docs/CHANGELOG.md)

### Community Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Wiki**: Community-maintained documentation and tips

### Professional Support

For enterprise deployments and custom integrations:

- **Email**: <support@jobops.dev>
- **Documentation**: <https://docs.jobops.dev>
- **Enterprise**: <https://enterprise.jobops.dev>

### Social Media

- **Twitter**: [@JobOpsApp](https://twitter.com/JobOpsApp)
- **LinkedIn**: [JobOps Company Page](https://linkedin.com/company/jobops)
- **Blog**: [blog.jobops.dev](https://blog.jobops.dev)

---

**Built with ❤️ for job seekers worldwide**

*Empowering career growth through intelligent automation*

**Version 1.0.0** | **Released 2025** | **Made with AI**
