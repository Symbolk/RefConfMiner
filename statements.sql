show databases;
use refactoring_analysis;
show tables;
describe merge_commit;
select * from project;
delete from project where id=1;
select * from merge_commit WHERE project_id=1 and is_conflicting=1;
select count(*) from merge_commit WHERE project_id=16;
select count(*) from merge_commit where is_conflicting=1 and project_id=1;
select count(*) from merge_commit where is_conflicting=1 and project_id=2;
select count(*) from refactoring where project_id=16;

select count(*) from refactoring_region where project_id=11;
select count(*) from conflicting_region where project_id=7;