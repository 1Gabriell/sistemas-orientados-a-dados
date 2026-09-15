SELECT
dados.ano AS ano,
dados.sigla_uf AS sigla_uf,
diretorio_sigla_uf.nome AS sigla_uf_nome,
dados.id_municipio AS id_municipio,
diretorio_id_municipio.nome AS id_municipio_nome,
dados.id_escola AS id_escola,
diretorio_id_escola.nome AS id_escola_nome,
dados.ensino AS ensino,
dados.anos_escolares AS anos_escolares,
dados.taxa_aprovacao AS taxa_aprovacao,
dados.indicador_rendimento AS indicador_rendimento,
dados.nota_saeb_media_padronizada AS nota_saeb_media_padronizada,
dados.ideb AS ideb,
dados.projecao AS projecao
FROM `basedosdados.br_inep_ideb.escola` AS dados
LEFT JOIN (
SELECT DISTINCT sigla, nome
FROM `basedosdados.br_bd_diretorios_brasil.uf`
) AS diretorio_sigla_uf
ON dados.sigla_uf = diretorio_sigla_uf.sigla
LEFT JOIN (
SELECT DISTINCT id_municipio, nome
FROM `basedosdados.br_bd_diretorios_brasil.municipio`
) AS diretorio_id_municipio
ON dados.id_municipio = diretorio_id_municipio.id_municipio
LEFT JOIN (
SELECT DISTINCT id_escola, nome, latitude, longitude
FROM `basedosdados.br_bd_diretorios_brasil.escola`
) AS diretorio_id_escola
ON dados.id_escola = diretorio_id_escola.id_escola
WHERE dados.ideb IS NOT NULL
AND dados.sigla_uf IN (
'AL',
'BA',
'CE',
'MA',
'PB',
'PE',
'PI',
'RN',
'SE'
);
