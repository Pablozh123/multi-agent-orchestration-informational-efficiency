"""Privater All-In Live-Bot (NICHT thesis-facing).

Dieses Paket liegt bewusst getrennt vom deterministischen Thesis-Kern.
Es dient einem privaten Experiment auf dem Polymarket All-In Mentions-Event
und ist keine thesis-facing Analyse. Ergebnisse landen unter
data/live/allin_july3/.

Standard ist Dry-Run: es werden keine echten Orders platziert und keine
Trading-Credentials geladen. Die Live-Ausfuehrung ueber py-clob-client ist
absichtlich nicht implementiert, bis sie ausdruecklich freigegeben wird
(siehe execution.LiveExecutor).
"""
