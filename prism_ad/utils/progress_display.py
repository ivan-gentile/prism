#!/usr/bin/env python3
"""
Sistema di visualizzazione progresso per PRISM-AD
Mostra messaggi eleganti in dissolvenza durante l'elaborazione
"""

import time
import threading
import sys
from typing import Optional, List
from datetime import datetime

class ProgressDisplay:
    """
    Sistema di visualizzazione progresso elegante per PRISM-AD
    Mostra fasi dell'analisi con animazioni e timing
    """
    
    def __init__(self, show_timing: bool = True, animation_speed: float = 0.3):
        self.show_timing = show_timing
        self.animation_speed = animation_speed
        self.current_phase = None
        self.phase_start_time = None
        self.total_start_time = None
        self.animation_running = False
        self.animation_thread = None
        self.web_tracker = None  # Web tracker per l'interfaccia
        
        # Fasi dell'analisi PRISM-AD
        self.phases = {
            "init": "Inizializzazione sistema PRISM-AD",
            "data_collection": "Raccolta e validazione dati paziente",
            "rag_analysis": "Consultazione base di evidenze cliniche",
            "agent_1": "Analisi Agente Clinico 1 - Valutazione iniziale",
            "agent_2": "Analisi Agente Clinico 2 - Biomarcatori",
            "agent_3": "Analisi Agente Clinico 3 - Fattori di rischio",
            "agent_4": "Analisi Agente Clinico 4 - Prognosi",
            "consensus": "Elaborazione consenso multi-agente",
            "final_report": "Preparazione report finale",
            "formatting": "Formattazione output professionale",
            "complete": "Analisi completata"
        }
        
        self.phase_descriptions = {
            "init": "Caricamento modelli e configurazioni",
            "data_collection": "Verifica completezza e coerenza dati clinici",
            "rag_analysis": "Ricerca evidenze in letteratura scientifica",
            "agent_1": "Valutazione clinica generale e staging",
            "agent_2": "Interpretazione profilo biomarcatori",
            "agent_3": "Identificazione fattori di rischio e protettivi",
            "agent_4": "Stima rischio e prognosi a 5 anni",
            "consensus": "Sintesi e validazione risultati multipli",
            "final_report": "Generazione report per neurologo e paziente",
            "formatting": "Applicazione formattazione medico-professionale",
            "complete": "Report pronto per consultazione"
        }
    
    def set_web_tracker(self, web_tracker):
        """Imposta il web tracker per l'interfaccia"""
        self.web_tracker = web_tracker
        
    def start_analysis(self):
        """Inizia il tracking dell'analisi completa"""
        self.total_start_time = datetime.now()
        print("\n" + "=" * 80)
        print("PRISM-AD - Sistema di Valutazione del Rischio Alzheimer")
        print("=" * 80)
        print(f"Avvio analisi: {self.total_start_time.strftime('%d/%m/%Y alle %H:%M:%S')}")
        print()
        
        if self.web_tracker:
            self.web_tracker.start_analysis({})
    
    def start_phase(self, phase_key: str):
        """Avvia una nuova fase dell'analisi"""
        if self.current_phase:
            self.end_phase()
        
        self.current_phase = phase_key
        self.phase_start_time = datetime.now()
        
        phase_name = self.phases.get(phase_key, f"Fase {phase_key}")
        description = self.phase_descriptions.get(phase_key, "")
        
        print(f"▶ {phase_name}")
        if description:
            print(f"  {description}")
        
        if self.web_tracker:
            self.web_tracker.start_phase(phase_key)
        
        # Avvia animazione di progresso
        self._start_animation()
    
    def end_phase(self):
        """Termina la fase corrente"""
        if not self.current_phase:
            return
        
        self._stop_animation()
        
        if self.phase_start_time and self.show_timing:
            duration = datetime.now() - self.phase_start_time
            duration_str = f"{duration.total_seconds():.1f}s"
            print(f"  ✓ Completata in {duration_str}")
        else:
            print("  ✓ Completata")
        
        print()
        self.current_phase = None
        self.phase_start_time = None
    
    def update_progress(self, message: str):
        """Aggiorna il messaggio di progresso della fase corrente"""
        self._stop_animation()
        print(f"  • {message}")
        
        if self.web_tracker:
            self.web_tracker.update_progress(message)
        
        self._start_animation()
    
    def complete_analysis(self):
        """Completa l'analisi e mostra statistiche finali"""
        if self.current_phase:
            self.end_phase()
        
        if self.total_start_time:
            total_duration = datetime.now() - self.total_start_time
            minutes = int(total_duration.total_seconds() // 60)
            seconds = total_duration.total_seconds() % 60
            
            print("=" * 80)
            print("ANALISI PRISM-AD COMPLETATA")
            print("=" * 80)
            print(f"Tempo totale: {minutes}m {seconds:.1f}s")
            print(f"Completata: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}")
            print()
    
    def _start_animation(self):
        """Avvia l'animazione di progresso"""
        if self.animation_running:
            return
        
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animate_progress, daemon=True)
        self.animation_thread.start()
    
    def _stop_animation(self):
        """Ferma l'animazione di progresso"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=0.5)
        
        # Pulisci la riga dell'animazione
        print("\r" + " " * 50 + "\r", end="", flush=True)
    
    def _animate_progress(self):
        """Animazione di progresso con puntini"""
        dots = ""
        while self.animation_running:
            for i in range(4):
                if not self.animation_running:
                    break
                dots = "." * i
                print(f"\r  Elaborazione{dots:<3}", end="", flush=True)
                time.sleep(self.animation_speed)
    
    def show_error(self, error_message: str):
        """Mostra un messaggio di errore"""
        self._stop_animation()
        print(f"  ✗ Errore: {error_message}")
        print()
    
    def show_warning(self, warning_message: str):
        """Mostra un messaggio di avvertimento"""
        print(f"  ⚠ Avvertimento: {warning_message}")

class ContextualProgressDisplay(ProgressDisplay):
    """
    Versione avanzata con messaggi contestuali per ogni agente
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Messaggi specifici per ogni agente
        self.agent_contexts = {
            "rag": {
                "start": "Consultazione letteratura scientifica",
                "progress": [
                    "Ricerca studi longitudinali su MCI",
                    "Analisi biomarker tau e amiloide",
                    "Valutazione fattori di rischio APOE",
                    "Sintesi evidenze cliniche"
                ]
            },
            "clinician": {
                "start": "Valutazione clinica specialistica",
                "progress": [
                    "Analisi anamnesi e sintomi",
                    "Interpretazione test cognitivi",
                    "Valutazione imaging cerebrale",
                    "Classificazione FDA staging"
                ]
            },
            "biomarker": {
                "start": "Analisi profilo biomarcatori",
                "progress": [
                    "Elaborazione valori Aβ42/Aβ40",
                    "Interpretazione p-Tau181",
                    "Valutazione NFL e GFAP",
                    "Correlazione pattern patologico"
                ]
            },
            "risk": {
                "start": "Calcolo rischio longitudinale",
                "progress": [
                    "Applicazione modelli predittivi",
                    "Analisi sopravvivenza Cox",
                    "Calcolo probabilità conversione",
                    "Stima intervalli di confidenza"
                ]
            },
            "consensus": {
                "start": "Elaborazione consenso multi-agente",
                "progress": [
                    "Raccolta valutazioni agenti",
                    "Risoluzione discordanze",
                    "Weighted voting algorithm",
                    "Validazione risultato finale"
                ]
            }
        }
    
    def start_agent_analysis(self, agent_type: str, agent_name: str = None):
        """Avvia l'analisi di un agente specifico con contesto"""
        display_name = agent_name or f"Agente {agent_type.title()}"
        context = self.agent_contexts.get(agent_type, {})
        
        phase_key = f"agent_{agent_type}"
        self.phases[phase_key] = f"Analisi {display_name}"
        self.phase_descriptions[phase_key] = context.get("start", "Elaborazione in corso")
        
        self.start_phase(phase_key)
        
        # Mostra progressi contestuali se disponibili
        if "progress" in context:
            threading.Thread(
                target=self._show_contextual_progress, 
                args=(context["progress"],), 
                daemon=True
            ).start()
    
    def _show_contextual_progress(self, progress_items: List[str]):
        """Mostra progressi contestuali per l'agente corrente"""
        for i, item in enumerate(progress_items):
            if not self.animation_running:
                break
            
            time.sleep(2.0 + i * 1.5)  # Timing realistico
            if self.animation_running:
                self._stop_animation()
                print(f"  • {item}")
                self._start_animation()

# Istanza globale per uso semplice
prism_progress = ContextualProgressDisplay()

def show_analysis_progress(func):
    """
    Decorator per mostrare automaticamente il progresso durante l'analisi
    """
    def wrapper(*args, **kwargs):
        prism_progress.start_analysis()
        try:
            result = func(*args, **kwargs)
            prism_progress.complete_analysis()
            return result
        except Exception as e:
            prism_progress.show_error(str(e))
            prism_progress.complete_analysis()
            raise
    return wrapper

# Funzioni di utilità per uso rapido
def start_phase(phase: str):
    """Avvia una fase dell'analisi"""
    prism_progress.start_phase(phase)

def end_phase():
    """Termina la fase corrente"""
    prism_progress.end_phase()

def update_progress(message: str):
    """Aggiorna il progresso della fase corrente"""
    prism_progress.update_progress(message)

def start_agent(agent_type: str, agent_name: str = None):
    """Avvia l'analisi di un agente"""
    prism_progress.start_agent_analysis(agent_type, agent_name)

if __name__ == "__main__":
    # Test del sistema di progresso
    print("Test sistema di progresso PRISM-AD...")
    
    progress = ContextualProgressDisplay()
    
    progress.start_analysis()
    
    # Simula fasi dell'analisi
    progress.start_phase("init")
    time.sleep(2)
    progress.end_phase()
    
    progress.start_phase("data_collection")
    progress.update_progress("Validazione dati anagrafici")
    time.sleep(1.5)
    progress.update_progress("Verifica biomarcatori")
    time.sleep(1.5)
    progress.end_phase()
    
    # Test agenti con contesto
    progress.start_agent_analysis("rag", "RAG Evidence Retrieval")
    time.sleep(5)
    progress.end_phase()
    
    progress.start_agent_analysis("clinician", "Clinician Assessment")
    time.sleep(4)
    progress.end_phase()
    
    progress.start_phase("consensus")
    time.sleep(3)
    progress.end_phase()
    
    progress.start_phase("final_report")
    time.sleep(2)
    progress.end_phase()
    
    progress.complete_analysis()
    print("Test completato!")
