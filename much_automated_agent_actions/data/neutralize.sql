UPDATE ai_provider
   SET api_key = NULL
 WHERE api_key IS NOT NULL;
