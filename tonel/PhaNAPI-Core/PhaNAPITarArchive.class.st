Class {
	#name : #PhaNAPITarArchive,
	#superclass : #Archive,
	#category : #'PhaNAPI-Core-Tar'
}

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
	member fileSize ~= 0 ifTrue: [
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

{ #category : #'instance creation' }
PhaNAPITarArchive >> wrapReadStream: binaryStream [
	^ binaryStream
]
