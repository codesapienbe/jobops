from jobops.models import MotivationLetter, PersonalInfo, GenericDocument, DocumentType, JobData
import logging
import json
from jobops.clients import BaseLLMBackend
from typing import Protocol

class LetterGenerator(Protocol):
    def generate(self, job_data: JobData, resume: str, language: str = "en") -> MotivationLetter: ...

class ConcreteLetterGenerator:
    def __init__(self, llm_backend: BaseLLMBackend):
        self.backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate(self, job_data: JobData, resume: str, language: str = "en") -> MotivationLetter:
        self._logger.info(f"Generating motivation letter in language: {language}")
        
        system_prompt = self._create_system_prompt(job_data.company, language)
        user_prompt = self._create_user_prompt(job_data, resume, language)
        
        try:
            content = self.backend.generate_response(user_prompt, system_prompt)
            return MotivationLetter(
                job_data=job_data,
                resume=resume,
                content=content,
                language=language
            )
        except Exception as e:
            self._logger.error(f"Error generating motivation letter: {e}")
            raise Exception(f"Failed to generate motivation letter: {str(e)}")
    
    def _create_system_prompt(self, company: str, language: str) -> str:
        prompts = {
            # English
            "en": f"""You are a professional career consultant. Write an authentic, compelling motivation letter for '{company}'.

GUIDELINES:
- Use proper salutation: 'Dear {company} team' or 'Dear Hiring Manager at {company}'
- Be genuine and honest - avoid generic company praise or clichés
- Focus on specific skills and experiences that match the role
- Show authentic interest in the position, not empty flattery
- Use clear, concise language with professional but warm tone
- Structure: 3-4 short paragraphs, 250-350 words total
- End with confident but respectful closing""",

            # Dutch
            "nl": f"""Je bent een professionele loopbaanadviseur. Schrijf een authentieke, overtuigende motivatiebrief voor '{company}'.

RICHTLIJNEN:
- Gebruik correcte aanhef: 'Geachte {company} team' of 'Geachte Hiring Manager bij {company}'
- Wees oprecht en eerlijk - vermijd generieke bedrijfslof of clichés
- Focus op specifieke vaardigheden en ervaring die passen bij de rol
- Toon authentieke interesse in de functie, geen lege vleierij
- Gebruik heldere, beknopte taal met professionele maar warme toon
- Structuur: 3-4 korte alinea's, 250-350 woorden totaal
- Eindig met zelfverzekerde maar respectvolle afsluiting""",

            # Turkish
            "tr": f"""Profesyonel bir kariyer danışmanısınız. '{company}' için samimi ve etkileyici bir motivasyon mektubu yazın.

KURALLAR:
- Doğru hitap kullanın: 'Sayın {company} ekibi' veya 'Sayın {company} İnsan Kaynakları Müdürü'
- Samimi ve dürüst olun - genel şirket övgüsü veya klişelerden kaçının
- Role uygun belirli beceri ve deneyimlere odaklanın
- Pozisyona gerçek ilgi gösterin, boş iltifatlar değil
- Net, özlü dil kullanın, profesyonel ama sıcak ton
- Yapı: 3-4 kısa paragraf, toplam 250-350 kelime
- Kendinden emin ama saygılı kapanışla bitirin""",

            # French
            "fr": f"""Vous êtes un conseiller en carrière professionnel. Rédigez une lettre de motivation authentique et convaincante pour '{company}'.

DIRECTIVES:
- Utilisez une salutation appropriée: 'Cher équipe de {company}' ou 'Cher responsable RH chez {company}'
- Soyez sincère et honnête - évitez les éloges génériques ou les clichés
- Concentrez-vous sur les compétences et expériences spécifiques qui correspondent au poste
- Montrez un intérêt authentique pour le poste, pas de flatterie vide
- Utilisez un langage clair et concis avec un ton professionnel mais chaleureux
- Structure: 3-4 paragraphes courts, 250-350 mots au total
- Terminez par une conclusion confiante mais respectueuse""",

            # German
            "de": f"""Sie sind ein professioneller Karriereberater. Verfassen Sie ein authentisches, überzeugendes Motivationsschreiben für '{company}'.

RICHTLINIEN:
- Verwenden Sie eine angemessene Anrede: 'Sehr geehrtes {company} Team' oder 'Sehr geehrte Personalverantwortliche bei {company}'
- Seien Sie aufrichtig und ehrlich - vermeiden Sie generisches Unternehmenslob oder Klischees
- Fokussieren Sie sich auf spezifische Fähigkeiten und Erfahrungen, die zur Stelle passen
- Zeigen Sie authentisches Interesse an der Position, keine leeren Schmeicheleien
- Verwenden Sie klare, prägnante Sprache mit professionellem aber warmem Ton
- Struktur: 3-4 kurze Absätze, 250-350 Wörter insgesamt
- Schließen Sie selbstbewusst aber respektvoll ab""",

            # Spanish
            "es": f"""Eres un consultor profesional de carrera. Escribe una carta de motivación auténtica y convincente para '{company}'.

PAUTAS:
- Usa saludo apropiado: 'Estimado equipo de {company}' o 'Estimado responsable de RRHH de {company}'
- Sé genuino y honesto - evita elogios genéricos de empresa o clichés
- Enfócate en habilidades y experiencias específicas que coincidan con el puesto
- Muestra interés auténtico en la posición, no adulación vacía
- Usa lenguaje claro y conciso con tono profesional pero cálido
- Estructura: 3-4 párrafos cortos, 250-350 palabras en total
- Termina con cierre confiado pero respetuoso""",

            # Italian
            "it": f"""Sei un consulente professionale di carriera. Scrivi una lettera di motivazione autentica e convincente per '{company}'.

LINEE GUIDA:
- Usa un saluto appropriato: 'Gentile team di {company}' o 'Gentile responsabile HR di {company}'
- Sii genuino e onesto - evita elogi generici all'azienda o cliché
- Concentrati su competenze ed esperienze specifiche che corrispondono al ruolo
- Mostra interesse autentico per la posizione, non adulazione vuota
- Usa un linguaggio chiaro e conciso con tono professionale ma caloroso
- Struttura: 3-4 paragrafi brevi, 250-350 parole totali
- Concludi con chiusura sicura ma rispettosa""",

            # Arabic
            "ar": f"""أنت مستشار مهني محترف. اكتب خطاب تحفيز أصيل ومقنع لشركة '{company}'.

التوجيهات:
- استخدم تحية مناسبة: 'فريق {company} المحترم' أو 'مسؤول الموارد البشرية المحترم في {company}'
- كن صادقاً وأميناً - تجنب المدح العام للشركة أو العبارات المبتذلة
- ركز على المهارات والخبرات المحددة التي تتناسب مع الوظيفة
- أظهر اهتماماً حقيقياً بالمنصب، وليس مجاملات فارغة
- استخدم لغة واضحة ومختصرة بنبرة مهنية ودافئة
- الهيكل: 3-4 فقرات قصيرة، 250-350 كلمة إجمالي
- اختتم بثقة ولكن باحترام""",

            # Portuguese
            "pt": f"""Você é um consultor profissional de carreira. Escreva uma carta de motivação autêntica e convincente para '{company}'.

DIRETRIZES:
- Use saudação apropriada: 'Prezada equipe da {company}' ou 'Prezado responsável de RH da {company}'
- Seja genuíno e honesto - evite elogios genéricos à empresa ou clichês
- Foque em habilidades e experiências específicas que correspondam ao cargo
- Mostre interesse autêntico na posição, não bajulação vazia
- Use linguagem clara e concisa com tom profissional mas caloroso
- Estrutura: 3-4 parágrafos curtos, 250-350 palavras no total
- Termine com fechamento confiante mas respeitoso""",

            # Polish
            "pl": f"""Jesteś profesjonalnym doradcą kariery. Napisz autentyczny, przekonujący list motywacyjny do '{company}'.

WYTYCZNE:
- Użyj odpowiedniego pozdrowienia: 'Szanowny zespół {company}' lub 'Szanowny kierownik HR w {company}'
- Bądź szczery i uczciwy - unikaj ogólnych pochwał firmy lub frazesów
- Skup się na konkretnych umiejętnościach i doświadczeniach pasujących do stanowiska
- Pokaż autentyczne zainteresowanie pozycją, nie puste pochlebstwa
- Używaj jasnego, zwięzłego języka z profesjonalnym ale ciepłym tonem
- Struktura: 3-4 krótkie akapity, łącznie 250-350 słów
- Zakończ pewnym ale pełnym szacunku zamknięciem""",

            # Russian
            "ru": f"""Вы профессиональный карьерный консультант. Напишите искреннее, убедительное мотивационное письмо для '{company}'.

РЕКОМЕНДАЦИИ:
- Используйте подходящее обращение: 'Уважаемая команда {company}' или 'Уважаемый HR-менеджер {company}'
- Будьте искренними и честными - избегайте общих похвал компании или клише
- Сосредоточьтесь на конкретных навыках и опыте, соответствующих должности
- Покажите подлинный интерес к позиции, а не пустую лесть
- Используйте четкий, лаконичный язык с профессиональным но теплым тоном
- Структура: 3-4 коротких абзаца, всего 250-350 слов
- Завершите уверенно но уважительно""",

            # Hebrew
            "he": f"""אתה יועץ קריירה מקצועי. כתב מכתב מוטיבציה אותנטי ומשכנע עבור '{company}'.

הנחיות:
- השתמש בברכה מתאימה: 'לכבוד צוות {company}' או 'לכבוד מנהל משאבי אנוש ב-{company}'
- היה כנה וישר - הימנע משבחים כלליים על החברה או קלישאות
- התמקד בכישורים וניסיון ספציפיים המתאימים לתפקיד
- הראה עניין אמיתי בתפקיד, לא חנופה ריקה
- השתמש בשפה ברורה ותמציתית בטון מקצועי אך חם
- מבנה: 3-4 פסקאות קצרות, סך הכל 250-350 מילים
- סיים בביטחון אך בכבוד""",

            # Greek
            "el": f"""Είστε επαγγελματίας σύμβουλος καριέρας. Γράψτε ένα αυθεντικό, πειστικό γράμμα κινήτρων για την '{company}'.

ΟΔΗΓΙΕΣ:
- Χρησιμοποιήστε κατάλληλο χαιρετισμό: 'Αγαπητή ομάδα {company}' ή 'Αγαπητέ υπεύθυνε HR στην {company}'
- Γίνετε γνήσιοι και ειλικρινείς - αποφύγετε γενικούς επαίνους εταιρείας ή κλισέ
- Εστιάστε σε συγκεκριμένες δεξιότητες και εμπειρίες που ταιριάζουν στο ρόλο
- Δείξτε αυθεντικό ενδιαφέρον για τη θέση, όχι κενή κολακεία
- Χρησιμοποιήστε σαφή, συνοπτική γλώσσα με επαγγελματικό αλλά ζεστό τόνο
- Δομή: 3-4 σύντομες παράγραφοι, συνολικά 250-350 λέξεις
- Τελειώστε με σίγουρο αλλά σεβαστό κλείσιμο"""
        }
        
        return prompts.get(language, prompts["en"])
    
    def _create_user_prompt(self, job_data: JobData, resume: str, language: str) -> str:
        templates = {
            "en": {
                "salutation": f"Dear {job_data.company} team," if job_data.company else "Dear Hiring Manager,",
                "intro": "Write a motivation letter for:",
                "sections": {
                    "position": "POSITION:",
                    "title": "Title:",
                    "company": "Company:",
                    "description": "Description:",
                    "requirements": "Requirements:",
                    "resume": "RESUME:",
                    "instruction": "Create a personal, authentic letter that demonstrates genuine fit for this specific role."
                }
            },
            "nl": {
                "salutation": f"Geachte {job_data.company} team," if job_data.company else "Geachte Hiring Manager,",
                "intro": "Schrijf een motivatiebrief voor:",
                "sections": {
                    "position": "FUNCTIE:",
                    "title": "Titel:",
                    "company": "Bedrijf:",
                    "description": "Beschrijving:",
                    "requirements": "Vereisten:",
                    "resume": "CV SAMENVATTING:",
                    "instruction": "Maak een persoonlijke, authentieke brief die echte geschiktheid voor deze specifieke rol toont."
                }
            },
            "tr": {
                "salutation": f"Sayın {job_data.company} ekibi," if job_data.company else "Sayın İnsan Kaynakları Müdürü,",
                "intro": "Şu pozisyon için motivasyon mektubu yazın:",
                "sections": {
                    "position": "POZİSYON:",
                    "title": "Başlık:",
                    "company": "Şirket:",
                    "description": "Açıklama:",
                    "requirements": "Gereksinimler:",
                    "resume": "ÖZGEÇMİŞ ÖZETİ:",
                    "instruction": "Bu spesifik rol için gerçek uygunluğu gösteren kişisel, samimi bir mektup oluşturun."
                }
            },
            "fr": {
                "salutation": f"Cher équipe de {job_data.company}," if job_data.company else "Cher responsable du recrutement,",
                "intro": "Rédigez une lettre de motivation pour:",
                "sections": {
                    "position": "POSTE:",
                    "title": "Titre:",
                    "company": "Entreprise:",
                    "description": "Description:",
                    "requirements": "Exigences:",
                    "resume": "RÉSUMÉ CV:",
                    "instruction": "Créez une lettre personnelle et authentique qui démontre une véritable adéquation pour ce rôle spécifique."
                }
            },
            "de": {
                "salutation": f"Sehr geehrtes {job_data.company} Team," if job_data.company else "Sehr geehrte Damen und Herren,",
                "intro": "Verfassen Sie ein Motivationsschreiben für:",
                "sections": {
                    "position": "STELLE:",
                    "title": "Titel:",
                    "company": "Unternehmen:",
                    "description": "Beschreibung:",
                    "requirements": "Anforderungen:",
                    "resume": "LEBENSLAUF ZUSAMMENFASSUNG:",
                    "instruction": "Erstellen Sie ein persönliches, authentisches Schreiben, das echte Eignung für diese spezifische Rolle zeigt."
                }
            },
            "ar": {
                "salutation": f"فريق {job_data.company} المحترم," if job_data.company else "مسؤول التوظيف المحترم,",
                "intro": "اكتب خطاب تحفيز لـ:",
                "sections": {
                    "position": "الوظيفة:",
                    "title": "المسمى:",
                    "company": "الشركة:",
                    "description": "الوصف:",
                    "requirements": "المتطلبات:",
                    "resume": "ملخص السيرة الذاتية:",
                    "instruction": "أنشئ خطاباً شخصياً وأصيلاً يظهر الملاءمة الحقيقية لهذا الدور المحدد."
                }
            }
        }
        template = templates.get(language, templates["en"])
        return f"""{template["intro"]}

{template["salutation"]}

{template["sections"]["position"]}
{template["sections"]["title"]} {job_data.title}
{template["sections"]["company"]} {job_data.company}
{template["sections"]["description"]} {job_data.description}
{template["sections"]["requirements"]} {job_data.requirements}

{template["sections"]["resume"]}
{resume}

{template["sections"]["instruction"]}"""


class DocumentExtractor:
    def __init__(self, llm_backend: BaseLLMBackend):
        self.llm_backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def extract_resume(self, raw_content: str, language: str = "en") -> str:
        system_prompt = """You are a professional resume optimization engine. Transform the raw input into a polished, ATS-friendly resume by:

1. STRUCTURE: Enforce standard sections (Summary, Experience, Education, Skills)
2. FORMATTING: Use clear headers, bullet points, and consistent spacing
3. CLARITY: Fix grammar/syntax errors while preserving original meaning
4. OPTIMIZATION: Highlight quantifiable achievements (e.g. 'Increased X by Y%')
5. HONESTY: Never add/remove content - only reorganize existing information
6. READABILITY: Ensure 1-2 page length with clean typography (10-12pt fonts)

Return ONLY the improved resume text with no commentary."""
        
        prompt = f"""Transform this raw resume into a professional document:

RAW CONTENT:
{raw_content[:6000]}

REQUIREMENTS:
- Use reverse chronological order
- Start bullet points with action verbs
- Remove personal pronouns
- Keep skills relevant to job market
- Standardize date formats (MM/YYYY-MM/YYYY)
- Eliminate redundancy and filler words
- Ensure ATS compatibility (no columns/graphics)"""

        try:
            cleaned_text = self.llm_backend.generate_response(prompt, system_prompt).strip()
            return cleaned_text
        except Exception as e:
            self._logger.error(f"Resume cleaning failed: {e}")
            return raw_content[:500]

    def extract_generic_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        output_schema = GenericDocument.model_json_schema()
        
        system_prompt = f"""You are a precision document parser. Extract and structure data from {doc_type.value} with:

1. ACCURACY: Preserve exact figures, names, and dates
2. CONTEXT: Maintain semantic relationships between sections
3. INTEGRITY: Never infer missing information
4. FORMAT: Return strict JSON matching schema exactly"""

        prompt = f"""Extract document data to JSON schema:

SCHEMA:
{json.dumps(output_schema, indent=2)}

DOCUMENT TYPE: {doc_type.value}
CONTENT:
{raw_content[:10000]}

RULES:
- Use null for missing fields
- Preserve original text casing
- No markdown/code blocks in output
- Escape special characters properly
- Validate JSON syntax strictly"""

        try:
            response = self.llm_backend.generate_response(prompt, system_prompt)
            cleaned_response = response.strip().removeprefix('``````').strip()
            doc_data = json.loads(cleaned_response)
            return GenericDocument(**doc_data)
        except Exception as e:
            self._logger.error(f"Document extraction failed: {e}")
            return self._create_fallback_document(raw_content, doc_type)

    def _create_fallback_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        return GenericDocument(
            content_type=doc_type.value,
            title=self._extract_title(raw_content),
            key_points=[],
            sections={},
            metadata={}
        )

    def _extract_name(self, text: str) -> str:
        return next((line.strip() for line in text.split('\n')[:5] if line.strip() and '@' not in line), "Unknown")

    def _extract_title(self, text: str) -> str:
        return next((line.strip() for line in text.split('\n')[:3] if line.strip()), "Untitled Document")

