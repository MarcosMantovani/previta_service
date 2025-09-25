-- set group sessions flag and external id
update
	multiplex_session ms
set 	
	is_group = True,
    external_id = concat(ms.payload->>'secondary_description', '@g.us')
where
	length(ms.payload->>'secondary_description') >= 18
;


-- set group channel identities flag
update
	multiplex_channelidentity mc2 	
set 	
	is_group = True
from
	multiplex_contact mc	
where
	mc2.contact_id  = mc.id
	and mc.payload->>'is_group' = 'true'
;


-- set contact created at to the first session created at
update
	multiplex_contact mc 
set
	created_at = (
		select
			created_at
		from
			multiplex_session ms 
		where
			ms.contact_id  = mc.id
		order by
			ms.created_at 
		limit 1
	)
where
	(
		select
			created_at
		from
			multiplex_session ms 
		where
			ms.contact_id  = mc.id
		order by
			ms.created_at 
		limit 1
	) is not null
	and created_at > (
		select
			created_at
		from
			multiplex_session ms 
		where
			ms.contact_id  = mc.id
		order by
			ms.created_at 
		limit 1
	)
;


-- create table to migrate channel identities
create table migrate_ci as
select 	
	co.phone,
	ci.id,
	ci.display_name,
	ci.contact_id,
	ci.created_at,
	ci.external_id,
	prev_ci.id as prev_ci_id,
	prev_ci.display_name as prev_ci_display_name,
	prev_ci.contact_id as prev_ci_contact_id,
	prev_ci.created_at as prev_ci_created_at,
	prev_ci.external_id as prev_ci_external_id
from
	multiplex_channelidentity ci 
inner join
	multiplex_contact co
	on co.id = ci.contact_id
inner join lateral
	(
		select
			prev_ci.id,
			prev_ci.display_name,
			prev_ci.contact_id,
			prev_ci.created_at,
			prev_ci.external_id
		from
			multiplex_channelidentity prev_ci
		inner join
			multiplex_contact prev_co 
			on prev_co.id = prev_ci.contact_id			
		where
			prev_co.phone = co.phone
			and prev_co.legacy_id is not null
		order by
			prev_co.created_at
		limit 1			
	) as prev_ci
	on true
where
	ci.external_id is not null
;	
	
-- migrate messages to correct channel identity
update
	multiplex_message mm
set 
	channel_identity_id = mci.prev_ci_id
from
	migrate_ci mci
where
	mci.id = mm.channel_identity_id
;

-- migrate sessions to correct channel identity
update
	multiplex_session ms
set 
	channel_identity_id = mci.prev_ci_id,
	contact_id = mci.prev_ci_contact_id
from
	migrate_ci mci
where
	mci.id = ms.channel_identity_id
;

-- delete channel identities that are not in the migrate_ci table
delete
	from
	multiplex_channelidentity mc
using
	migrate_ci mci
where 
	mci.id = mc.id
;

-- update channel identities external id to the new one
update
	multiplex_channelidentity mc
set 
	external_id = mci.external_id
from
	migrate_ci mci
where
	mci.prev_ci_id = mc.id
;

-- delete contact organizations from wrong contacts
delete from
	multiplex_contact_organizations mcorg
using
	migrate_ci mci
where 
	mci.contact_id = mcorg.contact_id
;

-- delete contacts that are not in the migrate_ci table
delete from
	multiplex_contact mco
using
	migrate_ci mci
where 
	mci.contact_id = mco.id
	and mco.legacy_id is null
;

-- update messages text to the caption if it is a media message
update
	multiplex_message mm
set
	text = payload->'data_media'->>'caption'
where
	mm."type" not in ('text', 'audio', 'contact')
	and length(trim(text)) <= 0
	and text is not null
	and length(payload->'data_media'->>'caption') > 0
;


with uniq as  (
	select
		co2.phone,
		mc2.channel_id
	from
		multiplex_channelidentity mc2
	inner join
		multiplex_contact co2
		on co2.id = mc2.contact_id
	group by
		co2.phone,
		mc2.channel_id
	having
		count(*) = 1			
)
update
	multiplex_channelidentity mc
set
	external_id = concat(co.phone, '@s.whatsapp.net')
from
	multiplex_contact co
where
	co.id = mc.contact_id
	and mc.external_id is null
	and co.phone ~ '^5'
	and length(co.phone) between 12 and 13
	and (
		select 
			phone
		from
			uniq
		where
			uniq.phone = co.phone
			and uniq.channel_id = mc.channel_id
		limit 1
	) is not null
;