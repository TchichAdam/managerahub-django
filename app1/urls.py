from django.urls import path
from . import views

urlpatterns = [
    # ─────────────────────────────────────────────
    # ACCUEIL
    # ─────────────────────────────────────────────
    path("", views.accueil, name="accueil"),

    # ─────────────────────────────────────────────
    # AUTHENTIFICATION
    # ─────────────────────────────────────────────
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", views.deconnexion, name="deconnexion"),

    # ─────────────────────────────────────────────
    # ESPACE CANDIDAT
    # ─────────────────────────────────────────────
    path("candidat/dashboard/", views.candidat_dashboard, name="candidat_dashboard"),
    path("candidat/profil/", views.candidat_profil, name="candidat_profil"),
    path("candidat/postuler/<int:offre_id>/", views.postuler, name="postuler"),

    # ─────────────────────────────────────────────
    # ESPACE ENTREPRISE
    # ─────────────────────────────────────────────
    path("entreprise/dashboard/", views.entreprise_dashboard, name="entreprise_dashboard"),
    path("entreprise/profil/", views.entreprise_profil, name="entreprise_profil"),
    path("entreprise/offre/creer/", views.creer_offre, name="creer_offre"),
    path("entreprise/offre/<int:offre_id>/modifier/", views.modifier_offre, name="modifier_offre"),
    path("entreprise/offre/<int:offre_id>/supprimer/", views.supprimer_offre, name="supprimer_offre"),
    path("entreprise/offre/<int:offre_id>/candidatures/", views.candidatures_offre, name="candidatures_offre"),
    path("entreprise/candidature/<int:candidature_id>/statut/", views.changer_statut_candidature, name="changer_statut_candidature"),

    # ─────────────────────────────────────────────
    # OFFRES (PUBLIC)
    # ─────────────────────────────────────────────
    path("offres/", views.liste_offres, name="liste_offres"),
    path("offres/<int:offre_id>/", views.detail_offre, name="detail_offre"),

    # ... (le reste de tes routes) ...
    
    path("candidats/", views.liste_candidats, name="liste_candidats"),
    path("candidatures/", views.liste_candidatures, name="liste_candidatures"),
    path("entreprises/", views.liste_entreprises, name="liste_entreprises"),
    path("utilisateurs/", views.liste_utilisateurs, name="liste_utilisateurs"),
]