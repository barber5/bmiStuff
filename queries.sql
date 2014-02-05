SELECT table_name AS tables, round(((data_length + index_length) / 1024 / 1024), 2) as sz FROM information_schema.TABLES ORDER BY (data_length + index_length) DESC;


SELECT sum(sz) FROM (SELECT table_name AS tables, round(((data_length + index_length) / 1024 / 1024), 2) as sz FROM information_schema.TABLES ORDER BY (data_length + index_length) DESC) as t1;

SELECT table_name AS tables, round(((index_length) / 1024 / 1024), 2) as sz FROM information_schema.TABLES ORDER BY (index_length) DESC;


 select * from stride5.mgrep into outfile '/ncbodata/tmp/emr/stride5-mgrep.txt';