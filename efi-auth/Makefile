##
# Project Title
#
# @file
# @version 0.1

# from https://git.kernel.org/pub/scm/linux/kernel/git/jejb/efitools.git/tree/Make.rules
MYGUID = 11111111-0000-1111-0000-123456789abc

%.crt:
	openssl req -new -x509 -newkey rsa:2048 -subj "/CN=$*/" -keyout $*.key -out $@ -days 3650 -nodes -sha256

%.esl: %.crt
	cert-to-efi-sig-list -g $(MYGUID) $< $@

getcert = $(shell if [ "$(1)" = "PK" -o "$(1)" = "KEK" ]; then echo "-c PK.crt -k PK.key"; else echo "-c KEK.crt -k KEK.key"; fi)
getvar = $(shell if [ "$(1)" = "PK" -o "$(1)" = "KEK" ]; then echo $(1); else echo db; fi)

%.auth: %.esl PK.crt KEK.crt
	sign-efi-sig-list $(call getcert,$*) $(call getvar,$*) $< $@

%-update.auth: %.esl PK.crt KEK.crt sign-efi-sig-list
	./sign-efi-sig-list -a $(call getcert,$*) $(call getvar,$*) $< $@

%-blacklist.auth: %-blacklist.esl KEK.crt sign-efi-sig-list
	./sign-efi-sig-list -a -c KEK.crt -k KEK.key dbx $< $@

tree/%: %
	mkdir -p $$(dirname $@)
	cp -av $< $@

clean:
	rm -rfv ./tree
	rm -fv disk.img

disk.img: tree/PK.auth tree/KEK.auth
	rm -f disk.img
	systemd-repart \
		--empty=create \
		--size=32M \
		--copy-source=./tree/ \
		--offline=true \
		--definitions=./repart.d/ \
		disk.img

.PHONY: clean

# end
