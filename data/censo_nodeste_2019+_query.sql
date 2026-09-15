WITH
dicionario_rede AS (
  SELECT
    chave AS chave_rede,
    valor AS descricao_rede
  FROM `basedosdados.br_inep_censo_escolar.dicionario`
  WHERE
    nome_coluna = 'rede'
    AND id_tabela = 'escola'
),

dicionario_tipo_localizacao AS (
  SELECT
    chave AS chave_tipo_localizacao,
    valor AS descricao_tipo_localizacao
  FROM `basedosdados.br_inep_censo_escolar.dicionario`
  WHERE
    nome_coluna = 'tipo_localizacao'
    AND id_tabela = 'escola'
),

dicionario_tipo_situacao_funcionamento AS (
  SELECT
    chave AS chave_tipo_situacao_funcionamento,
    valor AS descricao_tipo_situacao_funcionamento
  FROM `basedosdados.br_inep_censo_escolar.dicionario`
  WHERE
    nome_coluna = 'tipo_situacao_funcionamento'
    AND id_tabela = 'escola'
)

SELECT
  dados.ano AS ano,
  dados.sigla_uf AS sigla_uf,
  dados.id_municipio AS id_municipio,
  diretorio_id_municipio.nome AS id_municipio_nome,
  dados.id_escola AS id_escola,
  descricao_rede AS rede,
  descricao_tipo_localizacao AS tipo_localizacao,
  descricao_tipo_situacao_funcionamento AS tipo_situacao_funcionamento,
  dados.agua_potavel AS agua_potavel,
  dados.agua_rede_publica AS agua_rede_publica,
  dados.energia_rede_publica AS energia_rede_publica,
  dados.esgoto_rede_publica AS esgoto_rede_publica,
  dados.lixo_servico_coleta AS lixo_servico_coleta,
  dados.area_verde AS area_verde,
  dados.banheiro_chuveiro AS banheiro_chuveiro,
  dados.biblioteca AS biblioteca,
  dados.cozinha AS cozinha,
  dados.dormitorio_aluno AS dormitorio_aluno,
  dados.laboratorio_ciencias AS laboratorio_ciencias,
  dados.laboratorio_informatica AS laboratorio_informatica,
  dados.laboratorio_educacao_profissional AS laboratorio_educacao_profissional,
  dados.quadra_esportes AS quadra_esportes,
  dados.refeitorio AS refeitorio,
  dados.sala_leitura AS sala_leitura,
  dados.quantidade_sala_utilizada_climatizada AS quantidade_sala_utilizada_climatizada,
  dados.desktop_aluno AS desktop_aluno,
  dados.internet_alunos AS internet_alunos,
  dados.quantidade_profissional_saude AS quantidade_profissional_saude,
  dados.quantidade_profissional_nutricionista AS quantidade_profissional_nutricionista,
  dados.quantidade_profissional_psicologo AS quantidade_profissional_psicologo,
  dados.quantidade_profissional_pedagogia AS quantidade_profissional_pedagogia,
  dados.profissional_assistente_social AS profissional_assistente_social,
  dados.alimentacao AS alimentacao,
  dados.material_pedagogico_multimidia AS material_pedagogico_multimidia,
  dados.material_pedagogico_infantil AS material_pedagogico_infantil,
  dados.material_pedagogico_cientifico AS material_pedagogico_cientifico,
  dados.material_pedagogico_musical AS material_pedagogico_musical,
  dados.material_pedagogico_artistica AS material_pedagogico_artistica,
  dados.orgao_gremio_estudantil AS orgao_gremio_estudantil,
  dados.diurno AS diurno,
  dados.noturno AS noturno,
  dados.quantidade_matricula_feminino AS quantidade_matricula_feminino,
  dados.quantidade_matricula_masculino AS quantidade_matricula_masculino,
  dados.quantidade_matricula_nao_declarada AS quantidade_matricula_nao_declarada,
  dados.quantidade_matricula_branca AS quantidade_matricula_branca,
  dados.quantidade_matricula_preta AS quantidade_matricula_preta,
  dados.quantidade_matricula_parda AS quantidade_matricula_parda,
  dados.quantidade_matricula_amarela AS quantidade_matricula_amarela,
  dados.quantidade_matricula_indigena AS quantidade_matricula_indigena,
  dados.quantidade_matricula_utiliza_transporte_publico AS quantidade_matricula_utiliza_transporte_publico

FROM `basedosdados.br_inep_censo_escolar.escola` AS dados

LEFT JOIN (
  SELECT DISTINCT id_municipio, nome
  FROM `basedosdados.br_bd_diretorios_brasil.municipio`
) AS diretorio_id_municipio
  ON dados.id_municipio = diretorio_id_municipio.id_municipio

LEFT JOIN `dicionario_rede`
  ON dados.rede = chave_rede

LEFT JOIN `dicionario_tipo_localizacao`
  ON dados.tipo_localizacao = chave_tipo_localizacao

LEFT JOIN `dicionario_tipo_situacao_funcionamento`
  ON dados.tipo_situacao_funcionamento = chave_tipo_situacao_funcionamento

WHERE dados.sigla_uf IN (
  'AL',
  'BA',
  'CE',
  'MA',
  'PB',
  'PE',
  'PI',
  'RN',
  'SE'
)
AND dados.ano IN (2019, 2021, 2023);
