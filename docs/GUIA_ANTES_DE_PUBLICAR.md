# Checklist real de publicação do AEVIA

**Não lance o site somente com os resultados dos testes locais.**

1. No Windows, execute `configurar_administrador.bat`, escolha uma senha de 16+ caracteres e reinicie o servidor.
2. Teste uma contribuição com foto, o acesso de moderação, aprovação e exclusão. Teste no celular.
3. Teste busca de pelo menos 3 municípios, uma rua no mapa e 2050. Verifique fontes e datas antes de atribuir fotos a lugares.
4. Escolha hospedagem com banco E imagens persistentes e backups automáticos; hospedar SQLite em disco temporário pode apagar contribuições ao reiniciar/deploy.
5. Configure o `.env` no host com `APP_ENV=production`, `PUBLIC_URL=https://...`, `ADMIN_PASSWORD`, `SESSION_SECRET`, e e-mail real de contato. Nunca suba `.env` nem `storage` para um repositório público.
6. Configure limitação anti-spam, logs sem dados pessoais, verificação de segurança, HTTPS e backups com teste de restauração. Ajuste termos de direitos autorais e LGPD com responsável.
7. Teste Wikimedia, IBGE, tiles OpenStreetMap, serviço de geocodificação e (caso ativada) IA diretamente na hospedagem final. Os resultados dependem de acesso e cotas dos provedores.
8. Execute `verificar_publicacao.bat`, que mostra pendências declaradas. Uma checagem verde não substitui teste ou revisão real.

Na entrega, somente o site local foi testado: **nenhum serviço externo foi validado pela rede deste ambiente, e nenhum site público foi criado**.

## Migrar dados da versão anterior

Se você já enviou fotos no AEVIA anterior, **não apague a pasta antiga**. Feche o AEVIA e faça backup de `storage/` e `.env` antes de trocar a instalação. Guarde a pasta inteira como segurança. Se ainda não enviou contribuições, extraia o ZIP novo em outra pasta e execute normalmente.
