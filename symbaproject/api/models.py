from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _

# Enums para usar nos modelos de personagem e outros
class Raca(models.TextChoices):
    HUMANO_AMBRIANO = 'HA', 'Humano Ambriano'
    HUMANO_BARBARO = 'HB', 'Humano Bárbaro'
    CAMBIANTE = 'CA', 'Cambiante'
    GOBLIN = 'GO', 'Goblin'
    OGRO = 'OG', 'Ogro'
    ELFO = 'EL', 'Elfo'
    ANAO = 'AN', 'Anão'
    HUMANO_SEQUESTRADO = 'HS', 'Humano Sequestrado'
    TROLL = 'TR', 'Troll'
    MORTO_VIVO = 'MV', 'Morto-vivo'

# Nível da habilidade que um personagem pode atingir.
class NivelHabilidade(models.TextChoices):
    NOVATO = 'N', 'Novato'
    ADEPTO = 'A', 'Adepto'
    MESTRE = 'M', 'Mestre'

# Tipos de ações que uma habilidade, equipamento ou poder podem ter.
class TipoAcao(models.TextChoices):
    ATIVA = 'A', 'Ativa'
    LIVRE = 'L', 'Livre'
    PASSIVA = 'P', 'Passiva'
    REACAO = 'R', 'Reação'
    ESPECIAL = 'E', 'Especial'

# Tipos de habilidade que um personagem pode atingir.
class TipoHabilidade(models.TextChoices):
    HABILIDADE = 'H', 'Habilidade'
    TRACO = 'T', 'Traço'
    PODER_MISTICO = 'P', 'Poder Místico'

# Tipos dos equipamentos, essas propriedades são específicas para serem utilizadas no sistema.
class TipoEquipamento(models.TextChoices):
    ARREMESSO = 'AR', 'Arremesso'
    CURTA = 'CU', 'Curta'
    DESARMADO = 'DE', 'Desarmado'
    LONGA = 'LO', 'Longa'
    PESADA = 'PE', 'Pesada'
    PROJETIL = 'PR', 'Projetil'
    UMA_MAO = 'UM', 'Uma Mão'
    ESCUDO = 'ES', 'Escudo'
    ANTIDOTO = 'AN', 'Antídoto'
    VENENO = 'VE', 'Veneno'
    LEVE = 'LE', 'Leve'
    MEDIA = 'ME', 'Média'
    COMUM = 'CO', 'Comum'

# Manager customizado para o modelo de usuário
class UsuarioManager(BaseUserManager):
    def create_user(self, login, email, senha=None, tipo='JOGADOR', **extra_fields):
        if not login:
            raise ValueError(_('O login deve ser informado'))
        if not email:
            raise ValueError(_('O email deve ser informado'))
        email = self.normalize_email(email)
        user = self.model(login=login, email=email, tipo=tipo, **extra_fields)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, email, senha, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(login, email, senha, tipo='ADMIN', **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPOS = (
        ('JOGADOR', 'Jogador'),
        ('MESTRE', 'Mestre'),
        ('ADMIN', 'Administrador'),
    )
    login = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPOS, default='JOGADOR')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['email']

    objects = UsuarioManager()

    def __str__(self):
        return self.login

# Perfil específico para Jogador
class JogadorPerfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_jogador')
    biografia = models.TextField(blank=True, null=True)
    fotoDePerfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)
    
    def adicionar_personagem(self, nome_personagem):
        if not nome_personagem:
            return False
            
        Personagem.objects.create(jogador=self, nome=nome_personagem)
        return True

    def listar_personagens(self):
        return list(self.personagens.all())

    def __str__(self):
        return self.usuario.login

class Habilidade(models.Model):
    nome = models.CharField(max_length=100)
    descricao_geral = models.TextField()
    tipo = models.CharField(
        max_length=1,
        choices=TipoHabilidade.choices,
    )

    def listar_descricoes(self):
        return {
            descricao.get_nivel_habilidade_display(): {
                'tipo_acao': descricao.get_tipo_acao_display(),
                'descricao': descricao.descricao
            } for descricao in self.descricoes.all()
        }

    def __str__(self):
        return self.nome

class DescricaoHabilidade(models.Model):
    habilidade = models.ForeignKey(
        Habilidade,
        on_delete=models.CASCADE,
        related_name='descricoes'
    )
    nivel_habilidade = models.CharField(
        max_length=1,
        choices=NivelHabilidade.choices,
        default=NivelHabilidade.NOVATO
    )
    tipo_acao = models.CharField(
        max_length=1,
        choices=TipoAcao.choices,
        default=TipoAcao.ATIVA
    )
    descricao = models.TextField()

    class Meta:
        unique_together = ('habilidade', 'nivel_habilidade')

    def save(self, *args, **kwargs):
        # Se estiver criando (ou seja, ainda não existe)
        if not self.pk and self.habilidade.descricoes.count() >= 3:
            raise ValueError("Não é possível adicionar mais de 3 descrições para a mesma habilidade.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Descrição {self.get_nivel_habilidade_display()} de {self.habilidade.nome}"

class Qualidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class EquipamentoBase(models.Model):
    """Catálogo do equipamento, ou seja, todos os equipamentos do jogo, mas sem ser específicado de qual personagem é."""
    nome = models.CharField(max_length=100)
    custo = models.JSONField(default=dict)
    tipo = models.CharField(max_length=2, choices=TipoEquipamento.choices, default=TipoEquipamento.COMUM)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Equipamento(models.Model):
    personagem = models.ForeignKey(
        'Personagem',
        on_delete=models.CASCADE,
        related_name='equipamentos',
        null=True,
        blank=True,
    )
    equipamento_base = models.ForeignKey(
        EquipamentoBase,
        on_delete=models.CASCADE,
        related_name='equipamentos',
        null=True,
        blank=True,
    )
    equipado = models.BooleanField(default=False)  # Se o personagem tá usando o equipamento

    def __str__(self):
        return f"{self.equipamento_base.nome} de {self.personagem.nome}"

class Elixir(Equipamento):
    efeito = models.TextField()

    def __str__(self):
        return f"{self.nome} (Efeito: {self.efeito})"

class ArmaBase(EquipamentoBase):
    dano = models.CharField(max_length=50)  # Ex: "1d6"
    qualidade = models.ForeignKey(
        Qualidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='armas_base'
    )

class Arma(Equipamento):
    arma_base = models.ForeignKey(
        ArmaBase,
        on_delete=models.CASCADE,
        related_name='armas',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.arma_base.nome} (Dano: {self.arma_base.dano})"

class ArmaduraBase(EquipamentoBase):
    protecao = models.CharField(max_length=50)  # Ex: "1d4"
    qualidade = models.ForeignKey(
        Qualidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='armaduras_base'
    )

class Armadura(Equipamento):
    armadura_base = models.ForeignKey(
        ArmaduraBase,
        on_delete=models.CASCADE,
        related_name='armaduras',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.armadura_base.nome} (Proteção: {self.armadura_base.protecao})"

class ArtefatoBase(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()

    def __str__(self):
        return self.titulo

class Artefato(models.Model):
    personagem = models.ForeignKey(
        'Personagem',
        on_delete=models.CASCADE,
        related_name='artefatos',
        null=True,
        blank=True
    )
    artefato_base = models.ForeignKey(
        ArtefatoBase,
        on_delete=models.CASCADE,
        related_name='artefatos',
        null=True,
        blank=True,
    )
    equipado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.artefato_base.titulo} ({self.personagem.nome if self.personagem else 'Sem Personagem'})"

class Poder(models.Model):
    artefato = models.ForeignKey(
        Artefato,
        on_delete=models.CASCADE,
        related_name='poderes'
    )
    nome = models.CharField(max_length=100)
    requesito = models.TextField()
    descricao = models.TextField()
    acao = models.CharField(
        max_length=1,
        choices=TipoAcao.choices,
        default=TipoAcao.ATIVA
    )
    corrupcao = models.CharField(max_length=50)  # Ex: "1d6"

    def __str__(self):
        return f"{self.nome} ({self.artefato.titulo})"

class Personagem(models.Model):
    jogador = models.ForeignKey(JogadorPerfil, on_delete=models.CASCADE, related_name='personagens')
    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField(default=18)
    experiencia = models.PositiveIntegerField(default=0)
    experiencia_nao_gasta = models.PositiveIntegerField(default=0)
    raca = models.CharField(max_length=2, choices=Raca.choices, default=Raca.HUMANO_AMBRIANO)
    ocupacao = models.CharField(max_length=100, blank=True, null=True)
    vitaliade_maxima = models.PositiveIntegerField(blank=True, null=True)
    vitalidade_atual = models.PositiveIntegerField(blank=True, null=True)
    limiar_de_dor = models.PositiveIntegerField(blank=True, null=True)
    corrupcao_permanente = models.PositiveIntegerField(default=0)
    corrupcao_temporaria = models.PositiveIntegerField(default=0)
    limiar_de_corrupcao = models.PositiveIntegerField(blank=True, null=True)
    sombra = models.CharField(max_length=100, blank=True, null=True)
    citacao = models.CharField(max_length=200, blank=True, null=True)

    # Atributos básicos do personagem, eles vão definir alguns dos atributos acima.
    astuto = models.PositiveBigIntegerField(default=10)
    discreto = models.PositiveBigIntegerField(default=10)
    persuasivo = models.PositiveBigIntegerField(default=10)
    preciso = models.PositiveBigIntegerField(default=10)
    rapido = models.PositiveBigIntegerField(default=10)
    resoluto = models.PositiveBigIntegerField(default=10)
    vigilante = models.PositiveBigIntegerField(default=10)
    vigoroso = models.PositiveBigIntegerField(default=10)
    habilidades_e_poderes = models.ManyToManyField(
        Habilidade,
        through='Aprende',
        related_name='personagens'
    )
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    aparencia = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_personagens/', blank=True, null=True)
    historico = models.TextField(blank=True, null=True)
    objetivo_pessoal = models.TextField(blank=True, null=True)
    amigos_e_companheiros = models.TextField(blank=True, null=True)
    armadura_equipada = models.OneToOneField(
        'Armadura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personagem_vestindo'
    )
    armas_equipadas = models.ManyToManyField(
        'Arma',
        blank=True,
        related_name='personagem_empunhando'
    )
    dinheiro = models.JSONField(default=dict) # Ex: {'taler': 1, 'xelins': 3, 'ortegas': 20}
    outras_riquezas = models.TextField(blank=True, null=True)


    def equipar_armadura(self, armadura):
        if armadura.personagem != self:
            raise ValueError("Essa armadura não pertence ao personagem.")
        self.armadura_equipada = armadura
        self.save()

    def equipar_arma(self, arma):
        if arma.personagem != self:
            raise ValueError("Essa arma não pertence ao personagem.")
        self.armas_equipadas.add(arma)
        self.save()

    def ganhar_experiencia(self, quantidade):
        self.experiencia += quantidade
        self.experiencia_nao_gasta += quantidade
        self.save()

    def remover_experiencia(self, quantidade):
        if quantidade > self.experiencia_nao_gasta:
            raise ValueError("Não é possível remover mais experiência do que a disponível.")
        self.experiencia_nao_gasta -= quantidade
        self.save()

    def remover_experiencia_total(self, quantidade):
        if quantidade > self.experiencia:
            raise ValueError("Não é possível remover mais experiência do que a total.")
        self.experiencia -= quantidade
        self.experiencia_nao_gasta -= quantidade
        self.save()

    def listar_habilidades(self):
        habilidades = self.aprende_set.select_related('habilidade')
        resultado = []
        for aprende in habilidades:
            nivel = aprende.get_nivel_display()
            habilidade = aprende.habilidade
            resultado.append({
                'nome': habilidade.nome,
                'descricao': habilidade.descricao_geral,
                'tipo': habilidade.tipo,
                'nivel': nivel,
            })
        return resultado

    def __str__(self):
        return f"{self.nome} ({self.jogador.usuario.login})"

class Aprende(models.Model):
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE)
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)
    nivel = models.CharField(
        max_length=1,
        choices=NivelHabilidade.choices,
        default=NivelHabilidade.NOVATO
    )

    class Meta:
        unique_together = ('personagem', 'habilidade')

    def promover_nivel(self):
        ordem = ['N', 'A', 'M']
        atual = ordem.index(self.nivel)
        if atual < 2:  # Se não for o nível máximo
            self.nivel = ordem[atual + 1]
            self.save()

    def rebaixar_nivel(self):
        ordem = ['N', 'A', 'M']
        atual = ordem.index(self.nivel)
        if atual > 0:
            self.nivel = ordem[atual - 1]
            self.save()

    def clean(self):
        super().clean()

        existe = Aprende.objects.filter(
            personagem=self.personagem,
            habilidade=self.habilidade
        ).exclude(pk=self.pk).exists()

        if existe:
            raise ValueError("Esse personagem já aprendeu essa habilidade, atualize o nível em vez de criar uma nova entrada.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.personagem.nome} - {self.habilidade.nome} ({self.get_nivel_display()})"

