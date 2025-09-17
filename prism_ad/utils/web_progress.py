#!/usr/bin/env python3
"""
Sistema di progresso per interfaccia web PRISM-AD
Gestisce streaming in tempo reale dei messaggi di progresso
"""

import time
import threading
import json
from datetime import datetime
from typing import Optional, List, Dict, Callable
from queue import Queue
import uuid

class WebProgressTracker:
    """
    Tracker di progresso per interfaccia web con streaming in tempo reale
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = None
        self.current_phase = None
        self.phase_start_time = None
        self.progress_queue = Queue()
        self.is_active = False
        self.callbacks = []
        
        # Fasi dell'analisi PRISM-AD per web
        self.web_phases = {
            "init": {
                "title": "Inizializzazione",
                "description": "Preparazione sistema PRISM-AD",
                "icon": "fa-cogs"
            },
            "data_validation": {
                "title": "Validazione Dati",
                "description": "Controllo completezza dati paziente",
                "icon": "fa-check-circle"
            },
            "evidence_search": {
                "title": "Ricerca Evidenze",
                "description": "Consultazione letteratura clinica",
                "icon": "fa-search"
            },
            "clinical_analysis": {
                "title": "Analisi Clinica",
                "description": "Valutazione specialistica multi-agente",
                "icon": "fa-user-md"
            },
            "biomarker_analysis": {
                "title": "Analisi Biomarcatori",
                "description": "Interpretazione profilo molecolare",
                "icon": "fa-microscope"
            },
            "risk_calculation": {
                "title": "Calcolo Rischio",
                "description": "Elaborazione modelli predittivi",
                "icon": "fa-calculator"
            },
            "consensus": {
                "title": "Consenso Multi-Agente",
                "description": "Sintesi valutazioni specialistiche",
                "icon": "fa-users"
            },
            "report_generation": {
                "title": "Generazione Report",
                "description": "Preparazione documento clinico",
                "icon": "fa-file-medical"
            },
            "formatting": {
                "title": "Formattazione",
                "description": "Finalizzazione output professionale",
                "icon": "fa-paint-brush"
            },
            "complete": {
                "title": "Analisi Completata",
                "description": "Report pronto per consultazione",
                "icon": "fa-check"
            }
        }
        
        # Messaggi specifici per ogni fase
        self.phase_messages = {
            "init": [
                "Caricamento modelli AI specializzati",
                "Inizializzazione sistema multi-agente",
                "Verifica configurazioni cliniche"
            ],
            "data_validation": [
                "Validazione dati anagrafici",
                "Controllo valori biomarcatori",
                "Verifica completezza anamnesi"
            ],
            "evidence_search": [
                "Ricerca studi longitudinali MCI",
                "Analisi evidenze su biomarcatori",
                "Consultazione linee guida FDA"
            ],
            "clinical_analysis": [
                "Valutazione sintomi cognitivi",
                "Interpretazione test neuropsicologici",
                "Analisi fattori di rischio"
            ],
            "biomarker_analysis": [
                "Elaborazione valori Aβ42/Aβ40",
                "Interpretazione p-Tau181",
                "Correlazione pattern patologico"
            ],
            "risk_calculation": [
                "Applicazione modelli Cox",
                "Calcolo probabilità conversione",
                "Stima intervalli confidenza"
            ],
            "consensus": [
                "Raccolta valutazioni agenti",
                "Risoluzione discordanze",
                "Validazione risultato finale"
            ],
            "report_generation": [
                "Generazione sezione medico",
                "Preparazione comunicazione paziente",
                "Compilazione appendice tecnica"
            ],
            "formatting": [
                "Applicazione template clinico",
                "Ottimizzazione layout",
                "Controllo qualità output"
            ]
        }
    
    def add_callback(self, callback: Callable):
        """Aggiunge callback per notifiche di progresso"""
        self.callbacks.append(callback)
    
    def _emit_progress(self, event_type: str, data: Dict):
        """Emette evento di progresso"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "data": data
        }
        
        # Aggiungi alla queue per streaming
        self.progress_queue.put(event)
        
        # Notifica callbacks
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Errore callback progresso: {e}")
    
    def start_analysis(self, patient_info: Optional[Dict] = None):
        """Inizia il tracking dell'analisi"""
        self.start_time = datetime.now()
        self.is_active = True
        
        self._emit_progress("analysis_started", {
            "message": "Analisi PRISM-AD avviata",
            "patient_info": patient_info,
            "estimated_duration": "2-3 minuti"
        })
    
    def start_phase(self, phase_key: str):
        """Avvia una nuova fase"""
        if self.current_phase:
            self.end_phase()
        
        self.current_phase = phase_key
        self.phase_start_time = datetime.now()
        
        phase_info = self.web_phases.get(phase_key, {
            "title": phase_key.title(),
            "description": "Elaborazione in corso",
            "icon": "fa-cog"
        })
        
        self._emit_progress("phase_started", {
            "phase": phase_key,
            "title": phase_info["title"],
            "description": phase_info["description"],
            "icon": phase_info["icon"]
        })
        
        # Avvia messaggi progressivi per la fase
        if phase_key in self.phase_messages:
            threading.Thread(
                target=self._show_phase_messages,
                args=(phase_key, self.phase_messages[phase_key]),
                daemon=True
            ).start()
    
    def end_phase(self):
        """Termina la fase corrente"""
        if not self.current_phase:
            return
        
        duration = None
        if self.phase_start_time:
            duration = (datetime.now() - self.phase_start_time).total_seconds()
        
        self._emit_progress("phase_completed", {
            "phase": self.current_phase,
            "duration": duration
        })
        
        self.current_phase = None
        self.phase_start_time = None
    
    def update_progress(self, message: str, details: Optional[str] = None):
        """Aggiorna il progresso della fase corrente"""
        print(f"🔧 DEBUG: WebProgressTracker.update_progress called with: '{message}'")
        self._emit_progress("progress_update", {
            "phase": self.current_phase,
            "message": message,
            "details": details
        })
    
    def complete_analysis(self, result_summary: Optional[Dict] = None):
        """Completa l'analisi"""
        if self.current_phase:
            self.end_phase()
        
        total_duration = None
        if self.start_time:
            total_duration = (datetime.now() - self.start_time).total_seconds()
        
        self._emit_progress("analysis_completed", {
            "message": "Analisi PRISM-AD completata con successo",
            "total_duration": total_duration,
            "result_summary": result_summary
        })
        
        self.is_active = False
    
    def show_error(self, error_message: str, phase: Optional[str] = None):
        """Mostra un errore"""
        self._emit_progress("error", {
            "phase": phase or self.current_phase,
            "message": error_message
        })
    
    def _show_phase_messages(self, phase_key: str, messages: List[str]):
        """Mostra messaggi progressivi per una fase"""
        for i, message in enumerate(messages):
            if not self.is_active or self.current_phase != phase_key:
                break
            
            # Timing realistico per i messaggi
            delay = 1.5 + (i * 0.8)
            time.sleep(delay)
            
            if self.is_active and self.current_phase == phase_key:
                self.update_progress(message)
    
    def get_progress_stream(self):
        """Generatore per streaming eventi Server-Sent Events"""
        while self.is_active or not self.progress_queue.empty():
            try:
                event = self.progress_queue.get(timeout=1.0)
                yield f"data: {json.dumps(event)}\n\n"
            except:
                # Heartbeat per mantenere connessione
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"

class WebProgressManager:
    """
    Manager globale per tracking progresso di sessioni multiple
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, WebProgressTracker] = {}
        self.cleanup_interval = 300  # 5 minuti
        
        # Avvia pulizia periodica
        threading.Thread(target=self._cleanup_sessions, daemon=True).start()
    
    def create_session(self, session_id: str = None) -> WebProgressTracker:
        """Crea una nuova sessione di tracking"""
        tracker = WebProgressTracker(session_id)
        self.active_sessions[tracker.session_id] = tracker
        return tracker
    
    def get_session(self, session_id: str) -> Optional[WebProgressTracker]:
        """Ottiene una sessione esistente"""
        return self.active_sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """Rimuove una sessione"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def _cleanup_sessions(self):
        """Pulizia periodica delle sessioni inattive"""
        while True:
            time.sleep(self.cleanup_interval)
            
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, tracker in self.active_sessions.items():
                if not tracker.is_active and tracker.start_time:
                    elapsed = (current_time - tracker.start_time).total_seconds()
                    if elapsed > self.cleanup_interval:
                        expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.remove_session(session_id)

# Istanza globale singleton
_web_progress_manager = None

def get_web_progress_manager():
    """Ottiene l'istanza singleton del manager"""
    global _web_progress_manager
    if _web_progress_manager is None:
        _web_progress_manager = WebProgressManager()
    return _web_progress_manager

def create_web_progress_tracker(session_id: str = None) -> WebProgressTracker:
    """Crea un nuovo tracker di progresso per la web app"""
    manager = get_web_progress_manager()
    return manager.create_session(session_id)

def get_web_progress_tracker(session_id: str) -> Optional[WebProgressTracker]:
    """Ottiene un tracker esistente"""
    manager = get_web_progress_manager()
    return manager.get_session(session_id)
