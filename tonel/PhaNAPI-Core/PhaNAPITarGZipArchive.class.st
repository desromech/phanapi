"
I am a TAR archive that is also gzipped.
"
Class {
	#name : #PhaNAPITarGZipArchive,
	#superclass : #PhaNAPITarArchive,
	#category : #'PhaNAPI-Core-Tar'
}

{ #category : #'instance creation' }
PhaNAPITarGZipArchive >> wrapReadStream: binaryStream [
	^ GZipReadStream on: binaryStream
]
