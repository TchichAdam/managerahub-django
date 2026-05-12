import hashlib
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.core.paginator import Paginator

from .models import Utilisateur, Candidat, Entreprise, Offre, Candidature


# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def hash_password(password):
    """Hash simple SHA-256 pour correspondre aux mots de passe existants en clair ou hashés."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_utilisateur_connecte(request):
    """Retourne l'objet Utilisateur depuis la session, ou None."""
    user_id = request.session.get('utilisateur_id')
    if not user_id:
        return None
    try:
        return Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        return None


def login_required_candidat(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_utilisateur_connecte(request)
        if not user or user.role != 'candidat':
            messages.error(request, "Connectez-vous en tant que candidat.")
            return redirect('connexion')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def login_required_entreprise(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_utilisateur_connecte(request)
        if not user or user.role != 'entreprise':
            messages.error(request, "Connectez-vous en tant qu'entreprise.")
            return redirect('connexion')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def login_required_any(view_func):
    def wrapper(request, *args, **kwargs):
        user = get_utilisateur_connecte(request)
        if not user:
            messages.error(request, "Veuillez vous connecter.")
            return redirect('connexion')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ─────────────────────────────────────────────
# ACCUEIL
# ─────────────────────────────────────────────

def accueil(request):
    offres_recentes = Offre.objects.select_related('entreprise').order_by('-id')[:6]
    nb_offres = Offre.objects.count()
    nb_entreprises = Entreprise.objects.count()
    nb_candidats = Candidat.objects.count()
    user = get_utilisateur_connecte(request)
    return render(request, 'app1/accueil.html', {
        'offres_recentes': offres_recentes,
        'nb_offres': nb_offres,
        'nb_entreprises': nb_entreprises,
        'nb_candidats': nb_candidats,
        'utilisateur': user,
    })


# ─────────────────────────────────────────────
# AUTHENTIFICATION
# ─────────────────────────────────────────────

def inscription(request):
    if get_utilisateur_connecte(request):
        return redirect('accueil')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        mot_de_passe = request.POST.get('mot_de_passe', '')
        role = request.POST.get('role', 'candidat')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'app1/inscription.html', {'role': role})

        # Créer l'utilisateur
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO utilisateurs (email, mot_de_passe, role) VALUES (%s, %s, %s)",
                [email, mot_de_passe, role]
            )
            cursor.execute("SELECT @@IDENTITY")
            user_id = int(cursor.fetchone()[0])

        if role == 'candidat':
            nom = request.POST.get('nom', '').strip()
            prenom = request.POST.get('prenom', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO candidats (utilisateur_id, nom, prenom, telephone) VALUES (%s, %s, %s, %s)",
                    [user_id, nom, prenom, telephone]
                )
        elif role == 'entreprise':
            nom_entreprise = request.POST.get('nom_entreprise', '').strip()
            ville = request.POST.get('ville', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            description = request.POST.get('description', '').strip()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO entreprises (utilisateur_id, nom_entreprise, description, ville, telephone) VALUES (%s, %s, %s, %s, %s)",
                    [user_id, nom_entreprise, description, ville, telephone]
                )

        messages.success(request, "Compte créé avec succès ! Connectez-vous.")
        return redirect('connexion')

    return render(request, 'app1/inscription.html')


def connexion(request):
    if get_utilisateur_connecte(request):
        return redirect('accueil')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        mot_de_passe = request.POST.get('mot_de_passe', '')

        try:
            user = Utilisateur.objects.get(email=email)
            # Accepte le mot de passe en clair (données de test) ou hashé
            if user.mot_de_passe == mot_de_passe or user.mot_de_passe == hash_password(mot_de_passe):
                request.session['utilisateur_id'] = user.id
                request.session['utilisateur_role'] = user.role
                request.session['utilisateur_email'] = user.email
                messages.success(request, f"Bienvenue !")

                if user.role == 'candidat':
                    return redirect('candidat_dashboard')
                elif user.role == 'entreprise':
                    return redirect('entreprise_dashboard')
                else:
                    return redirect('accueil')
            else:
                messages.error(request, "Mot de passe incorrect.")
        except Utilisateur.DoesNotExist:
            messages.error(request, "Aucun compte avec cet email.")

    return render(request, 'app1/connexion.html')


def deconnexion(request):
    request.session.flush()
    messages.success(request, "Vous êtes déconnecté.")
    return redirect('accueil')


# ─────────────────────────────────────────────
# OFFRES (PUBLIC)
# ─────────────────────────────────────────────

def liste_offres(request):
    offres = Offre.objects.select_related('entreprise').order_by('-id')

    # Filtres
    q = request.GET.get('q', '')
    ville = request.GET.get('ville', '')
    domaine = request.GET.get('domaine', '')
    type_contrat = request.GET.get('type_contrat', '')

    if q:
        offres = offres.filter(titre__icontains=q)
    if ville:
        offres = offres.filter(ville__icontains=ville)
    if domaine:
        offres = offres.filter(domaine__icontains=domaine)
    if type_contrat:
        offres = offres.filter(type_contrat=type_contrat)

    # Pagination
    paginator = Paginator(offres, 8)
    page = request.GET.get('page', 1)
    offres_page = paginator.get_page(page)

    # Valeurs distinctes pour les filtres
    villes = Offre.objects.values_list('ville', flat=True).distinct().exclude(ville__isnull=True).exclude(ville='')
    domaines = Offre.objects.values_list('domaine', flat=True).distinct().exclude(domaine__isnull=True).exclude(domaine='')
    types = Offre.objects.values_list('type_contrat', flat=True).distinct().exclude(type_contrat__isnull=True).exclude(type_contrat='')

    return render(request, 'app1/liste_offres.html', {
        'offres': offres_page,
        'villes': villes,
        'domaines': domaines,
        'types': types,
        'q': q, 'ville': ville, 'domaine': domaine, 'type_contrat': type_contrat,
        'utilisateur': get_utilisateur_connecte(request),
    })


def detail_offre(request, offre_id):
    offre = get_object_or_404(Offre.objects.select_related('entreprise'), id=offre_id)
    user = get_utilisateur_connecte(request)
    deja_postule = False
    if user and user.role == 'candidat':
        try:
            candidat = Candidat.objects.get(utilisateur_id=user.id)
            deja_postule = Candidature.objects.filter(candidat=candidat, offre=offre).exists()
        except Candidat.DoesNotExist:
            pass
    return render(request, 'app1/detail_offre.html', {
        'offre': offre,
        'deja_postule': deja_postule,
        'utilisateur': user,
    })


# ─────────────────────────────────────────────
# ESPACE CANDIDAT
# ─────────────────────────────────────────────

@login_required_candidat
def candidat_dashboard(request):
    user = get_utilisateur_connecte(request)
    candidat = get_object_or_404(Candidat, utilisateur_id=user.id)
    candidatures = Candidature.objects.filter(candidat=candidat).select_related('offre__entreprise').order_by('-id')
    nb_en_attente = candidatures.filter(statut='En attente').count()
    nb_accepte = candidatures.filter(statut='Accepté').count()
    nb_refuse = candidatures.filter(statut='Refusé').count()
    return render(request, 'app1/candidat/dashboard.html', {
        'candidat': candidat,
        'candidatures': candidatures,
        'nb_en_attente': nb_en_attente,
        'nb_accepte': nb_accepte,
        'nb_refuse': nb_refuse,
        'utilisateur': user,
    })


@login_required_candidat
def postuler(request, offre_id):
    user = get_utilisateur_connecte(request)
    candidat = get_object_or_404(Candidat, utilisateur_id=user.id)
    offre = get_object_or_404(Offre, id=offre_id)

    if Candidature.objects.filter(candidat=candidat, offre=offre).exists():
        messages.warning(request, "Vous avez déjà postulé à cette offre.")
        return redirect('detail_offre', offre_id=offre_id)

    if request.method == 'POST':
        # Upload CV
        cv_file = request.FILES.get('cv')
        lettre_file = request.FILES.get('lettre_motivation')

        cv_path = candidat.cv
        lettre_path = candidat.lettre_motivation

        from django.conf import settings as django_settings
        import uuid

        if cv_file:
            ext = os.path.splitext(cv_file.name)[1]
            filename = f"cv_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(django_settings.MEDIA_ROOT, 'cvs', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb+') as f:
                for chunk in cv_file.chunks():
                    f.write(chunk)
            cv_path = f"cvs/{filename}"

        if lettre_file:
            ext = os.path.splitext(lettre_file.name)[1]
            filename = f"lettre_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(django_settings.MEDIA_ROOT, 'cvs', filename)
            with open(save_path, 'wb+') as f:
                for chunk in lettre_file.chunks():
                    f.write(chunk)
            lettre_path = f"cvs/{filename}"

        # Mettre à jour le candidat si nouveaux fichiers
        if cv_file or lettre_file:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE candidats SET cv=%s, lettre_motivation=%s WHERE id=%s",
                    [cv_path, lettre_path, candidat.id]
                )

        # Créer la candidature
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO candidatures (candidat_id, offre_id, statut) VALUES (%s, %s, %s)",
                [candidat.id, offre.id, 'En attente']
            )

        messages.success(request, "Candidature envoyée avec succès !")
        return redirect('candidat_dashboard')

    return render(request, 'app1/candidat/postuler.html', {
        'offre': offre,
        'candidat': candidat,
        'utilisateur': user,
    })


@login_required_candidat
def candidat_profil(request):
    user = get_utilisateur_connecte(request)
    candidat = get_object_or_404(Candidat, utilisateur_id=user.id)

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE candidats SET nom=%s, prenom=%s, telephone=%s WHERE id=%s",
                [nom, prenom, telephone, candidat.id]
            )
        messages.success(request, "Profil mis à jour !")
        return redirect('candidat_profil')

    return render(request, 'app1/candidat/profil.html', {
        'candidat': candidat,
        'utilisateur': user,
    })


# ─────────────────────────────────────────────
# ESPACE ENTREPRISE
# ─────────────────────────────────────────────

@login_required_entreprise
def entreprise_dashboard(request):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)
    offres = Offre.objects.filter(entreprise=entreprise).order_by('-id')
    nb_candidatures = Candidature.objects.filter(offre__entreprise=entreprise).count()
    nb_en_attente = Candidature.objects.filter(offre__entreprise=entreprise, statut='En attente').count()
    return render(request, 'app1/entreprise/dashboard.html', {
        'entreprise': entreprise,
        'offres': offres,
        'nb_candidatures': nb_candidatures,
        'nb_en_attente': nb_en_attente,
        'utilisateur': user,
    })


@login_required_entreprise
def creer_offre(request):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        domaine = request.POST.get('domaine', '').strip()
        ville = request.POST.get('ville', '').strip()
        type_contrat = request.POST.get('type_contrat', '').strip()

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO offres (entreprise_id, titre, description, domaine, ville, type_contrat, date_publication) VALUES (%s, %s, %s, %s, %s, %s, GETDATE())",
                [entreprise.id, titre, description, domaine, ville, type_contrat]
            )
        messages.success(request, "Offre publiée avec succès !")
        return redirect('entreprise_dashboard')

    return render(request, 'app1/entreprise/creer_offre.html', {
        'entreprise': entreprise,
        'utilisateur': user,
    })


@login_required_entreprise
def modifier_offre(request, offre_id):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)
    offre = get_object_or_404(Offre, id=offre_id, entreprise=entreprise)

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        domaine = request.POST.get('domaine', '').strip()
        ville = request.POST.get('ville', '').strip()
        type_contrat = request.POST.get('type_contrat', '').strip()

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE offres SET titre=%s, description=%s, domaine=%s, ville=%s, type_contrat=%s WHERE id=%s",
                [titre, description, domaine, ville, type_contrat, offre.id]
            )
        messages.success(request, "Offre mise à jour !")
        return redirect('entreprise_dashboard')

    return render(request, 'app1/entreprise/modifier_offre.html', {
        'offre': offre,
        'utilisateur': user,
    })


@login_required_entreprise
def supprimer_offre(request, offre_id):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)
    offre = get_object_or_404(Offre, id=offre_id, entreprise=entreprise)

    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM candidatures WHERE offre_id=%s", [offre.id])
            cursor.execute("DELETE FROM offres WHERE id=%s", [offre.id])
        messages.success(request, "Offre supprimée.")
        return redirect('entreprise_dashboard')

    return render(request, 'app1/entreprise/supprimer_offre.html', {
        'offre': offre,
        'utilisateur': user,
    })


@login_required_entreprise
def candidatures_offre(request, offre_id):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)
    offre = get_object_or_404(Offre, id=offre_id, entreprise=entreprise)
    candidatures = Candidature.objects.filter(offre=offre).select_related('candidat').order_by('-id')

    return render(request, 'app1/entreprise/candidatures_offre.html', {
        'offre': offre,
        'candidatures': candidatures,
        'utilisateur': user,
    })


@login_required_entreprise
def changer_statut_candidature(request, candidature_id):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)
    candidature = get_object_or_404(
        Candidature.objects.select_related('offre__entreprise'),
        id=candidature_id,
        offre__entreprise=entreprise
    )

    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in ['En attente', 'Accepté', 'Refusé', 'Convoqué']:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE candidatures SET statut=%s WHERE id=%s",
                    [nouveau_statut, candidature.id]
                )
            messages.success(request, f"Statut mis à jour : {nouveau_statut}")

    return redirect('candidatures_offre', offre_id=candidature.offre.id)


@login_required_entreprise
def entreprise_profil(request):
    user = get_utilisateur_connecte(request)
    entreprise = get_object_or_404(Entreprise, utilisateur_id=user.id)

    if request.method == 'POST':
        nom_entreprise = request.POST.get('nom_entreprise', '').strip()
        description = request.POST.get('description', '').strip()
        ville = request.POST.get('ville', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE entreprises SET nom_entreprise=%s, description=%s, ville=%s, telephone=%s WHERE id=%s",
                [nom_entreprise, description, ville, telephone, entreprise.id]
            )
        messages.success(request, "Profil mis à jour !")
        return redirect('entreprise_profil')

    return render(request, 'app1/entreprise/profil.html', {
        'entreprise': entreprise,
        'utilisateur': user,
    })


# ─────────────────────────────────────────────
# VUES ADMIN (simples)
# ─────────────────────────────────────────────

def liste_candidats(request):
    user = get_utilisateur_connecte(request)
    candidats = Candidat.objects.select_related('utilisateur').all()
    return render(request, 'app1/admin/liste_candidats.html', {
        'candidats': candidats, 'utilisateur': user,
    })


def liste_utilisateurs(request):
    user = get_utilisateur_connecte(request)
    utilisateurs = Utilisateur.objects.all().order_by('-date_creation')
    return render(request, 'app1/admin/liste_utilisateurs.html', {
        'utilisateurs': utilisateurs, 'utilisateur': user,
    })


def liste_entreprises(request):
    user = get_utilisateur_connecte(request)
    entreprises = Entreprise.objects.all()
    return render(request, 'app1/admin/liste_entreprises.html', {
        'entreprises': entreprises, 'utilisateur': user,
    })


def liste_candidatures(request):
    user = get_utilisateur_connecte(request)
    candidatures = Candidature.objects.select_related('candidat', 'offre__entreprise').order_by('-id')
    return render(request, 'app1/admin/liste_candidatures.html', {
        'candidatures': candidatures, 'utilisateur': user,
    })