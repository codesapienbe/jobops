from __future__ import annotations

from typing import Dict
from kivy.storage.jsonstore import JsonStore


LANGS = {
    "en": {
        "app.title": "JobOps App",
        "nav.position_details": "Position Details",
        "nav.job_requirements": "Job Requirements",
        "nav.company_information": "Company Information",
        "nav.skills_matrix": "Skills Matrix",
        "nav.application_materials": "Application Materials",
        "nav.interview_schedule": "Interview Schedule",
        "nav.interview_preparation": "Interview Preparation",
        "nav.communication_log": "Communication Log",
        "nav.key_contacts": "Key Contacts",
        "nav.interview_feedback": "Interview Feedback",
        "nav.offer_details": "Offer Details",
        "nav.rejection_analysis": "Rejection Analysis",
        "nav.privacy_policy": "Privacy Policy",
        "nav.lessons_learned": "Lessons Learned",
        "nav.performance_metrics": "Performance Metrics",
        "nav.advisor_review": "Advisor Review",
        "nav.application_summary": "Application Summary",
        "settings.title": "Settings",
        "common.save": "Save",
        "common.next": "Next",
    },
    "nl": {
        "app.title": "JobOps App",
        "nav.position_details": "Functiegegevens",
        "nav.job_requirements": "Functie-eisen",
        "nav.company_information": "Bedrijfsinformatie",
        "nav.skills_matrix": "Vaardighedenmatrix",
        "nav.application_materials": "Sollicitatiemateriaal",
        "nav.interview_schedule": "Interviewplanning",
        "nav.interview_preparation": "Interviewvoorbereiding",
        "nav.communication_log": "Communicatielog",
        "nav.key_contacts": "Belangrijke Contacten",
        "nav.interview_feedback": "Interview Feedback",
        "nav.offer_details": "Aanbiedingsdetails",
        "nav.rejection_analysis": "Afwijzingsanalyse",
        "nav.privacy_policy": "Privacybeleid",
        "nav.lessons_learned": "Lessen",
        "nav.performance_metrics": "Prestaties",
        "nav.advisor_review": "Adviesreview",
        "nav.application_summary": "Samenvatting",
        "settings.title": "Instellingen",
        "common.save": "Opslaan",
        "common.next": "Volgende",
    },
    "fr": {
        "app.title": "JobOps App",
        "nav.position_details": "Détails du poste",
        "nav.job_requirements": "Exigences du poste",
        "nav.company_information": "Informations sur l'entreprise",
        "nav.skills_matrix": "Matrice des compétences",
        "nav.application_materials": "Documents de candidature",
        "nav.interview_schedule": "Planning d'entretien",
        "nav.interview_preparation": "Préparation d'entretien",
        "nav.communication_log": "Journal des communications",
        "nav.key_contacts": "Contacts clés",
        "nav.interview_feedback": "Retour d'entretien",
        "nav.offer_details": "Détails de l'offre",
        "nav.rejection_analysis": "Analyse du rejet",
        "nav.privacy_policy": "Politique de confidentialité",
        "nav.lessons_learned": "Leçons",
        "nav.performance_metrics": "Indicateurs",
        "nav.advisor_review": "Avis du conseiller",
        "nav.application_summary": "Résumé",
        "settings.title": "Paramètres",
        "common.save": "Enregistrer",
        "common.next": "Suivant",
    },
    "tr": {
        "app.title": "JobOps Uygulaması",
        "nav.position_details": "Pozisyon Detayları",
        "nav.job_requirements": "İş Gereksinimleri",
        "nav.company_information": "Şirket Bilgileri",
        "nav.skills_matrix": "Yetenek Matrisi",
        "nav.application_materials": "Başvuru Belgeleri",
        "nav.interview_schedule": "Mülakat Takvimi",
        "nav.interview_preparation": "Mülakat Hazırlığı",
        "nav.communication_log": "İletişim Günlüğü",
        "nav.key_contacts": "Önemli Kişiler",
        "nav.interview_feedback": "Mülakat Geri Bildirimi",
        "nav.offer_details": "Teklif Detayları",
        "nav.rejection_analysis": "Red Analizi",
        "nav.privacy_policy": "Gizlilik Politikası",
        "nav.lessons_learned": "Çıkarılan Dersler",
        "nav.performance_metrics": "Performans Metrikleri",
        "nav.advisor_review": "Danışman İncelemesi",
        "nav.application_summary": "Başvuru Özeti",
        "settings.title": "Ayarlar",
        "common.save": "Kaydet",
        "common.next": "İleri",
    },
}


class I18N:
    def __init__(self, store: JsonStore):
        self.store = store
        self.lang = self.store.get("i18n")["lang"] if self.store.exists("i18n") else "en"

    def t(self, key: str) -> str:
        return LANGS.get(self.lang, LANGS["en"]).get(key, key)

    def set_language(self, lang: str) -> None:
        if lang not in LANGS:
            lang = "en"
        self.lang = lang
        self.store.put("i18n", lang=self.lang)
