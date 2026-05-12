# Update for GitHub language detection
from django.db import models


class Utilisateur(models.Model):
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=50)  # 'candidat' | 'entreprise' | 'admin'
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "utilisateurs"
        managed = False

    def __str__(self):
        return self.email


class Candidat(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        db_column='utilisateur_id',
        related_name='candidat_profil',
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    cv = models.CharField(max_length=255, blank=True, null=True)
    lettre_motivation = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "candidats"
        managed = False

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Entreprise(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        db_column='utilisateur_id',
        related_name='entreprise_profil',
    )
    nom_entreprise = models.CharField(max_length=150)
    description = models.CharField(max_length=500, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = "entreprises"
        managed = False

    def __str__(self):
        return self.nom_entreprise


class Offre(models.Model):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        db_column='entreprise_id',
        related_name='offres',
    )
    titre = models.CharField(max_length=150)
    description = models.CharField(max_length=1000)
    domaine = models.CharField(max_length=100, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    type_contrat = models.CharField(max_length=50, blank=True, null=True)
    date_publication = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "offres"
        managed = False

    def __str__(self):
        return self.titre


class Candidature(models.Model):
    candidat = models.ForeignKey(
        Candidat,
        on_delete=models.CASCADE,
        db_column='candidat_id',
        related_name='candidatures',
    )
    offre = models.ForeignKey(
        Offre,
        on_delete=models.CASCADE,
        db_column='offre_id',
        related_name='candidatures',
    )
    date_postulation = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='En attente')

    class Meta:
        db_table = "candidatures"
        managed = False

    def __str__(self):
        return f"{self.candidat} → {self.offre}"
