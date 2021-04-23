"
I am a facade for some PhaNAPI core utility methods.

"
Class {
	#name : #PhaNAPI,
	#superclass : #Object,
	#classInstVars : [
		'uniqueInstance'
	],
	#category : #'PhaNAPI-Core-LibrarySolving'
}

{ #category : #'library path' }
PhaNAPI class >> fullLibraryPathForCurrentPlatform: libraryName package: packageName [
	^ self uniqueInstance fullLibraryPathForCurrentPlatform: libraryName package: packageName
]

{ #category : #accessing }
PhaNAPI class >> uniqueInstance [
	^ uniqueInstance ifNil: [ uniqueInstance := self new ]
]

{ #category : #archives }
PhaNAPI >> decompressLibraryArchive: archive [
	| archiveFileRef archiveFullName |
	archiveFileRef := archive asFileReference.
	archiveFullName := archiveFileRef fullName.
	(archiveFullName endsWith: '.zip') ifTrue: [
		^ ZipArchive new
			readFrom: archiveFileRef;
			extractAllTo: self librariesDirectory
	].
	(archiveFullName endsWith: '.tar') ifTrue: [
		^ PhaNAPITarArchive unzip: archiveFileRef to: self librariesDirectory
	].
	((archiveFullName endsWith: '.tar.gz') or: [ archiveFullName endsWith: '.tgz' ]) ifTrue: [
		^ PhaNAPITarGZipArchive unzip: archiveFileRef to: self librariesDirectory
	].
	self error: 'Unsupported library archive format.'
]

{ #category : #directories }
PhaNAPI >> downloadsDirectory [
	^ self phanapiDirectory / #downloads
]

{ #category : #'library path' }
PhaNAPI >> fullLibraryName: libraryName forPlatform: platform [
	^ platform dynamicLibraryPrefix , libraryName , platform dynamicLibrarySuffix
]

{ #category : #'library path' }
PhaNAPI >> fullLibraryPathForCurrentPlatform: libraryName package: packageName [
	| fullLibraryName path |
	fullLibraryName := self fullLibraryName: libraryName forPlatform: Smalltalk os.

	path := Smalltalk imageDirectory / fullLibraryName.
	path isFile ifTrue: [ ^ path ].
		
	path := self librariesDirectory / packageName / fullLibraryName.
	path isFile ifTrue: [ ^ path ].

	path := self librariesDirectory / packageName / #lib / fullLibraryName.
	path isFile ifTrue: [ ^ path ].

	path := self librariesDirectory / fullLibraryName.
	path isFile ifTrue: [ ^ path ].

	path := self librariesDirectory / #lib / fullLibraryName.
	path isFile ifTrue: [ ^ path ].

	^ nil
]

{ #category : #directories }
PhaNAPI >> librariesDirectory [
	^ self phanapiDirectory / #libs
]

{ #category : #directories }
PhaNAPI >> phanapiDirectory [
	^ FileLocator localDirectory / #phanapi
]
