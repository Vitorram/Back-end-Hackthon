from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.database import SessionLocal
from backend.models.equipment import Equipment
from backend.models.equipment_history import EquipmentHistory
from backend.models.escola import Escola
from backend.models.usuario import Usuario
from backend.core.security import hash_password

SCHOOLS = [
    ("CAR-MOCK-001", "EMEF Prof. Antonio de Freitas Avelar", "Travessao"),
    ("CAR-MOCK-002", "EMEF Prof. Alaor Xavier Junqueira", "Indaia"),
    ("CAR-MOCK-003", "EMEF Prof. Jorge Passos", "Tinga"),
    ("CAR-MOCK-004", "EMEF Prof. Luiz Ribeiro Muniz", "Massaguacu"),
    ("CAR-MOCK-005", "EMEI/EMEF Prof. Oswaldo Ferreira", "Pereque-Mirim"),
    ("CAR-MOCK-006", "CEI Prof. Maria Aparecida Ujio", "Morro do Algodao"),
    ("CAR-MOCK-007", "EMEF Prof. Maria Thereza de Souza Castro", "Centro"),
    ("CAR-MOCK-008", "EMEF Prof. Benedito Inacio Soares", "Porto Novo"),
    ("CAR-MOCK-009", "EMEF Prof. Carlos Altero Ortega", "Casa Branca"),
    ("CAR-MOCK-010", "EMEF Prof. Maria Aparecida de Carvalho", "Olaria"),
    ("CAR-MOCK-011", "EMEF Prof. Luiz Silvar do Prado", "Tabatinga"),
    ("CAR-MOCK-012", "EMEI Prof. Sonia Maria de Souza", "Martim de Sa"),
]

TABLET_COUNTS = [36, 28, 42, 24, 31, 18, 34, 27, 22, 19, 15, 21]
NOTEBOOK_COUNTS = [8, 7, 10, 6, 7, 4, 8, 5, 5, 4, 3, 4]
COMPUTER_COUNTS = [18, 16, 22, 14, 15, 8, 20, 13, 11, 10, 8, 9]
STATUS_CYCLE = ["EM_USO", "EM_USO", "EM_USO", "DISPONIVEL", "EM_MANUTENCAO", "DEFEITUOSO"]

OTHER_EQUIPMENT = [
    ("Impressoras", "HP", "LaserJet Pro M404dw", "Secretaria", 2),
    ("Projetores", "Epson", "PowerLite E20 3400 Lumens", "Sala Multimidia", 3),
    ("Dispositivos de conectividade", "TP-Link", "Switch Gigabit 24 portas", "Rack de Rede", 2),
]


def upsert_admin(db):
    user = db.query(Usuario).filter(Usuario.email == "gestor@caragua.sp.gov.br").first()
    if not user:
        user = Usuario(
            nome="Gestor Tecnologia Educacional",
            matricula="CAR-MOCK-ADM",
            email="gestor@caragua.sp.gov.br",
            senha_hash=hash_password("123456"),
            perfil="SUPER_ADMIN",
            escola_id=None,
        )
        db.add(user)

    user.ativo = True
    user.aprovado = True
    user.pode_ver_dashboard = True
    user.pode_transferir = True
    user.pode_criar_equipamento = True
    user.pode_editar_equipamento = True
    user.pode_abrir_chamado = True
    user.pode_gerenciar_usuarios = True
    db.commit()
    db.refresh(user)
    return user


def upsert_schools(db):
    result = []
    for codigo, nome, bairro in SCHOOLS:
        school = db.query(Escola).filter(Escola.codigo == codigo).first()
        if not school:
            school = Escola(codigo=codigo, nome=nome)
            db.add(school)
        school.endereco = f"Bairro {bairro}, Caraguatatuba - SP"
        result.append(school)

    db.commit()
    for school in result:
        db.refresh(school)
    return result


def create_equipment_if_missing(db, school, tipo, marca, modelo, sala, index, status):
    prefix = {
        "Tablets": "TAB",
        "Notebooks": "NTB",
        "Computadores": "CPU",
        "Impressoras": "IMP",
        "Projetores": "PRO",
        "Dispositivos de conectividade": "RED",
    }[tipo]
    codigo = f"{school.codigo}-{prefix}-{index:03d}"

    existing = db.query(Equipment).filter(Equipment.codigo_interno == codigo).first()
    if existing:
        return False

    equipment = Equipment(
        patrimonio=codigo,
        codigo_interno=codigo,
        tipo=tipo,
        marca=marca,
        modelo=modelo,
        numero_serie=f"SN-{codigo}",
        data_aquisicao=date(2025, ((index - 1) % 9) + 1, 15),
        status=status,
        escola_atual_id=school.id,
        sala_atual=sala,
        observacoes=(
            "Dado mockado para demonstracao do agente SIGTEC em Caraguatatuba. "
            f"Unidade: {school.nome}."
        ),
    )
    db.add(equipment)
    db.flush()
    db.add(
        EquipmentHistory(
            equipamento_id=equipment.id,
            usuario_id=None,
            tipo_evento="CRIADO",
            descricao=f"Carga mockada criada para apresentacao: {codigo}.",
        )
    )
    return True


def seed_equipments(db, schools):
    created = 0
    for school_index, school in enumerate(schools):
        ranges = [
            (TABLET_COUNTS[school_index], "Tablets", "Samsung", "Galaxy Tab A8 Educacional 64GB", "Carrinho de Tablets"),
            (NOTEBOOK_COUNTS[school_index], "Notebooks", "Lenovo", "ThinkPad E14 Educacional", "Coordenacao Pedagogica"),
            (COMPUTER_COUNTS[school_index], "Computadores", "Dell", "OptiPlex 3080", "Laboratorio de Informatica"),
        ]

        for amount, tipo, marca, modelo, sala in ranges:
            for index in range(1, amount + 1):
                status = STATUS_CYCLE[(index + school_index) % len(STATUS_CYCLE)]
                created += int(create_equipment_if_missing(db, school, tipo, marca, modelo, sala, index, status))

        start_index = 300
        for tipo, marca, modelo, sala, amount in OTHER_EQUIPMENT:
            for offset in range(amount):
                status = "EM_USO" if offset % 2 == 0 else "DISPONIVEL"
                created += int(create_equipment_if_missing(db, school, tipo, marca, modelo, sala, start_index + offset, status))
            start_index += 20

    db.commit()
    return created


def main():
    db = SessionLocal()
    try:
        admin = upsert_admin(db)
        schools = upsert_schools(db)
        created = seed_equipments(db, schools)
        print("Seed mock Caraguatatuba finalizado.")
        print(f"Admin: {admin.email} / 123456")
        print(f"Escolas mockadas: {len(schools)}")
        print(f"Tablets no cenario: {sum(TABLET_COUNTS)}")
        print(f"Equipamentos novos nesta execucao: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
