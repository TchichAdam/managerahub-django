from django.contrib import admin
from .models import Candidat, Candidature, Entreprise, Offre, Utilisateur

admin.site.site_header = "Gestion des Candidats"
admin.site.site_title = "Admin Gestion des Candidats"
admin.site.index_title = "Administration"


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "role", "date_creation")
    search_fields = ("email", "role")
    list_filter = ("role",)


@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    list_display = ("id", "prenom", "nom", "telephone", "utilisateur")
    search_fields = ("prenom", "nom", "telephone", "utilisateur__email")


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("id", "nom_entreprise", "ville", "telephone", "utilisateur")
    search_fields = ("nom_entreprise", "ville", "utilisateur__email")


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ("id", "titre", "entreprise", "ville", "type_contrat", "date_publication")
    search_fields = ("titre", "ville", "domaine", "entreprise__nom_entreprise")
    list_filter = ("type_contrat", "ville", "date_publication")


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ("id", "candidat", "offre", "statut", "date_postulation")
    search_fields = ("candidat__nom", "candidat__prenom", "offre__titre", "statut")
    list_filter = ("statut", "date_postulation")
