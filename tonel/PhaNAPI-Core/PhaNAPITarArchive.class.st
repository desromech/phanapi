"
I am a class for reading and doing basic decompression of TAR archives. Unfortunately, I do not have support for proper decompression file attributes.
"
Class {
	#name : #PhaNAPITarArchive,
	#superclass : #Archive,
	#instVars : [
		'decompressionPath',
		'lastLongLink'
	],
	#category : #'PhaNAPI-Core-Tar'
}

{ #category : #unzipping }
PhaNAPITarArchive class >> unzip: archiveStreamOrFile [
	^ self unzip: archiveStreamOrFile to: FileSystem workingDirectory
]

{ #category : #unzipping }
PhaNAPITarArchive class >> unzip: archiveStreamOrFile to: targetPath [
	^ self new unzip: archiveStreamOrFile to: targetPath
]

{ #category : #parsing }
PhaNAPITarArchive >> isZeroRecord: record [
	1 to: 512 do: [ :i | (record at: i) ~= 0 ifTrue: [ ^ false ] ].
	^ true
]

{ #category : #private }
PhaNAPITarArchive >> memberClass [
	^ PhaNAPITarArchiveMember
]

{ #category : #'instance creation' }
PhaNAPITarArchive >> readFrom: aStreamOrFileName [
	| rawStream stream |
	rawStream := aStreamOrFileName isStream
		ifTrue: [ aStreamOrFileName ]
		ifFalse: [ aStreamOrFileName asFileReference binaryReadStream ].
		
	[
		stream := self wrapReadStream: rawStream.
		self readTarMembersFrom: stream
	] ensure: [
		aStreamOrFileName isStream ifFalse: [
			rawStream close
		]
	]
	

]

{ #category : #parsing }
PhaNAPITarArchive >> readTarMemberWithHeader: recordData from: stream [
	| member |
	member := PhaNAPITarArchiveMember new readHeaderFrom: recordData.
	member typeFlag = $L ifTrue: [ 
		member readContentFrom: stream.
		lastLongLink := member decodeLongLink.
		^ self
	].

	lastLongLink ifNotNil: [
		member setLongLinkValue: lastLongLink.
		lastLongLink := nil
	].

	decompressionPath ifNotNil: [
		member readContentFrom: stream intoTargetPath: decompressionPath
	] ifNil: [
		member readContentFrom: stream
	].
	self addMember: member
]

{ #category : #parsing }
PhaNAPITarArchive >> readTarMembersFrom: stream [
	| zeroRecordCount recordData |
	zeroRecordCount := 0.
	[stream atEnd] whileFalse: [ 
		recordData := stream next: 512.
		(self isZeroRecord: recordData) ifTrue: [
			zeroRecordCount := zeroRecordCount + 1.
			zeroRecordCount == 2 ifTrue: [
				^ 0
			]
		] ifFalse: [
			zeroRecordCount := 0.
			self readTarMemberWithHeader: recordData from: stream
		]
	]

]

{ #category : #unzipping }
PhaNAPITarArchive >> unzip: archiveStreamOrFile to: targetPath [
	decompressionPath := targetPath asFileReference.
	decompressionPath ensureCreateDirectory.
	self readFrom: archiveStreamOrFile
]

{ #category : #'instance creation' }
PhaNAPITarArchive >> wrapReadStream: binaryStream [
	^ binaryStream
]
