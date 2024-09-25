# prep

``` sh

# grab snakeoil keys
cp PkKek-1-snakeoil.pem PkKek-1-snakeoil.crt

make clean
make clean-disk

# generate data
# signing keys: sign.crt and the snakeoil key
# initial dbx blacklists bogus.crt, and an update which blacklists other-bogus.crt
make dataset SIGNING_KEYS='sign.crt PkKek-1-snakeoil.crt' BLACKLIST_KEYS='bogus.crt'

# prepare disk for enrolling keys
make tree/db.auth
make tree/dbx-blacklist.auth
make disk.img
```


# QEMU

``` sh
cp OVMF_VARS.fd OVMF_VARS.test.fd

# run without snapshot mode
qemu-system-x86_64 -enable-kvm -smp 4 -m 2048 -cpu host -machine q35 -global ICH9-LPC.disable_s3=1 \
        -drive file=./OVMF_CODE.secboot.fd,if=pflash,format=raw,unit=0,readonly=on \
        -drive file=./OVMF_VARS.test.fd,if=pflash,format=raw \
        -drive file=efi-auth/disk.img,if=none,id=disk1,snapshot=on \
        -device virtio-blk-pci,drive=disk1,bootindex=1 
        
# device configuration -> secure boot -> custom
# 1. enroll PK
# 2. enroll KEK
# 3. enroll DB
# 4. enroll DBX?

# reset
# pwoeroff
```


# EFI

## efitools

``` sh
$ sudo efitools.tool efi-readvar   
Variable PK, length 811                                   
PK: List 0, type X509                                           
    Signature 0, size 783, owner 8be4df61-93ca-11d2-aa0d-00e098032b8c
        Subject:                            
            CN=PK                                                      
        Issuer:                                                      
            CN=PK                                           
Variable KEK, length 813
KEK: List 0, type X509                                      
    Signature 0, size 785, owner 00000000-0000-0000-0000-000000000000
        Subject:                                                                                                                                                                               
            CN=KEK               
        Issuer:
            CN=KEK
Variable db, length 1640
db: List 0, type X509
    Signature 0, size 787, owner 11111111-0000-1111-0000-123456789abc
        Subject:
            CN=sign
        Issuer:
            CN=sign
db: List 1, type X509
    Signature 0, size 797, owner 11111111-0000-2222-0000-000000000000
        Subject:
            O=Snake Oil
        Issuer:
            O=Snake Oil
Variable dbx, length 817
dbx: List 0, type X509
    Signature 0, size 789, owner 11111111-0000-1111-0000-123456789abc
        Subject:
            CN=bogus
        Issuer:
            CN=bogus
Variable MokList has no entries
```

or manually importing from `*.auth` files:

``` sh
root@localhost:/home/maciek-borzecki# efitools.tool efi-updatevar -f PK.auth PK
root@localhost:/home/maciek-borzecki# efitools.tool efi-updatevar -f KEK.auth KEK
root@localhost:/home/maciek-borzecki# efitools.tool efi-updatevar -f db.auth db
root@localhost:/home/maciek-borzecki# efitools.tool efi-updatevar -f dbx-update-blacklist.auth
```

Variarbles may be marked as immutable, switch them back to mutable:

``` sh
chattr -i /sys/firmware/efi/efivars/dbx-d719b2cb-3d3a-4596-a3bc-dad00e67656f 
```

### quirks/notes

- crucial difference if payload is built for append or write
- cannot import an empty esl to dbx (?)

## fwupd

``` sh
maciek-borzecki@localhost:~$ sudo fwupd.fwupdtool get-devices                                                                                                                                   
Loading…                 [*****                                  ]14:35:34.806 FuPluginUefiCapsule  cannot find default ESP: No valid 'EspLocation' specified in /snap/fwupd/6368/etc/fwupd/fwupd.conf
Loading…                 [************************************** ]
WARNING: UEFI capsule updates not available or enabled in firmware setup                       
See https://github.com/fwupd/fwupd/wiki/PluginFlag:capsules-unsupported for more information.
WARNING: This package has not been validated, it may not work properly.
QEMU Standard PC (Q35 + ICH9, 2009)                                             
│                                              
...
├─UEFI dbx:                                              
│     Device ID:          362301da643102b9f38477387e2193e57abaa590                                                                                                                             
│     Summary:            UEFI revocation database              
│     Current version:    0                                                                                                                                                                    
│     Minimum Version:    0                                      
│     Vendor:             UEFI:Linux Foundation                                             
│     Install Duration:   1 second                                         
│     GUID:               c8fa151a-b08d-5945-80ba-06dfb62481d9 ← UEFI\CRT_45C7F7514B85E8CACEFDBC55EEE345BCFE6511AEF5A1EE48D12A24C0A6A0D2B0&ARCH_X64
│     Device Flags:       • Internal device                                   
│                         • Updatable                           
│                         • Needs a reboot after installation   
│                        • Device is usable for the duration of the update
│                         • Only version upgrades are allowed   
│                         • Signed Payload                                                                                                                                                     
...
```

The GUID line contains SHA256 of KEK which signed the DBX

``` sh
$ sudo snap run --shell fwupd
root@localhost:/home/maciek-borzecki# cd $SNAP
root@localhost:/snap/fwupd/6368# ./bin/dbxtool  -l
   1: {11111111-0000-1111-0000-123456789abc} {x509} ca4fbfb454920b25fbf07e2385242eba4e110024ab3d1c55883d78128b4400da

```

GUID is constructed using an identifier eg.
`UEFI\CRT_45C7F7514B85E8CACEFDBC55EEE345BCFE6511AEF5A1EE48D12A24C0A6A0D2B0&ARCH_X64`
which is constructed at runtime. 

``` python
import uuid
print(uuid.uuid5(uuid.NAMESPACE_DNS, r"UEFI\CRT_45C7F7514B85E8CACEFDBC55EEE345BCFE6511AEF5A1EE48D12A24C0A6A0D2B0&ARCH_X64"))
c8fa151a-b08d-5945-80ba-06dfb62481d9
```

LVFS metadata firmware identifier must use the same GUID to match it with the
update. Use the following template:

``` xml
<?xml version="1.0" encoding="UTF-8"?>
<component type="firmware">
  <id>org.canonical.dbx.x64.firmware</id>
  <name>Secure Boot dbx (test)</name>
  <name_variant_suffix>x64</name_variant_suffix>
  <summary>DBX update</summary>
  <provides>
    <!-- must match GUID of KEK -->
    <firmware type="flashed">#### KEK GUID ####</firmware>
  </provides>
  <url type="homepage">https://uefi.org/revocationlistfile</url>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>LicenseRef-proprietary</project_license>
  <categories>
    <category>X-Configuration</category>
    <category>X-System</category>
  </categories>
  <custom>
    <value key="LVFS::VersionFormat">number</value>
    <value key="LVFS::UpdateProtocol">org.uefi.dbx</value>
  </custom>
  <releases>
    <release version="1" date="2024-09-24" urgency="high">
      <description>
        test update
      </description>
      <artifacts>
        <artifact type="source">
          <filename>dbx-update-blacklist.auth</filename>
          <checksum type="sha256">#### CHECKSUM ####</checksum>
        </artifact>
      </artifacts>
    </release>
  </releases>
  <requires>
    <id compare="ge" version="1.9.1">org.freedesktop.fwupd</id>
  </requires>
</component>
```

Pack everything into a cab file:

``` sh
$ gcab -c -v dbx-v1.cab dbx.auth dbx.auth.metainfo.xml
dbx.auth
dbx.auth.metainfo.xml
```

and place in the vendor directory:

``` sh
cp dbx-v1.cab /var/snap/fwupd/common/share/fwupd/remotes.d/vendor/firmware/
fwupd.fwupdtool refresh
```

### Update

To update

``` sh
fwupd.fwupdtool refresh
fwupd.fwupdtool update --force --verbose 362301da643102b9f38477387e2193e57abaa590
```

No reboot necessary though. Verify with efi-readvar:


``` sh
root@localhost:/home/maciek-borzecki# efitools.tool efi-readvar -v dbx
Variable dbx, length 1646
dbx: List 0, type X509
    Signature 0, size 789, owner 11111111-0000-1111-0000-000000000000
        Subject:
            CN=bogus
        Issuer:
            CN=bogus
dbx: List 1, type X509
    Signature 0, size 801, owner 11111111-0000-1111-0000-000000000000
        Subject:
            CN=other-bogus
        Issuer:
            CN=other-bogus
```


## Links

- LVFS metadata https://lvfs.readthedocs.io/en/latest/metainfo.html
- LVFS uploading firmware https://lvfs.readthedocs.io/en/latest/upload.html
- fwupd remotes https://github.com/fwupd/fwupd/blob/main/data/remotes.d/README.md
