
#include <string.h>
#include <iostream>


unsigned int IntelToMot16(unsigned short val)
{
	return ((val & 0xFF00) >> 8) | ((val & 0xFF) << 8);
}


unsigned int IntelToMot32(unsigned int val)
{
	return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) | ((val >> 8) & 0xFF00) | ( val >> 24);
}

#pragma pack(1)

struct SPSD_Header
{
	SPSD_Header(int w = 1, int h = 1)
	:mVer(IntelToMot16(1))
	,mChan(IntelToMot16(3))
	,mHeight(IntelToMot32(w))
	,mWidth(IntelToMot32(h))
	,mDepth(IntelToMot16(8))
	,mMode(IntelToMot16(3))
	,mColourDataLen(0)
	,mResourceDataLen(0)
	{
		for (int i = 0; i < 6; ++i) mReserved[i] = 0;
		memcpy(mSIG, "8BPS", 4);
	}

	void deMot()
	{
		mVer = IntelToMot16(mVer);
		mChan = IntelToMot16(mChan);
		mHeight = IntelToMot32(mHeight);
		mWidth = IntelToMot32(mWidth);
		mDepth = IntelToMot16(mDepth);
		mMode = IntelToMot16(mMode);
		mColourDataLen = IntelToMot32(mColourDataLen);
		mResourceDataLen = IntelToMot32(mResourceDataLen);
	}

	char 		  mSIG[4];
	short  		  mVer;
	unsigned char mReserved[6];
	short 		  mChan;
	int  		  mHeight;
	int  		  mWidth;
	short  		  mDepth;
	short 		  mMode; //The color mode of the file. Supported values are: Bitmap = 0; Grayscale = 1; Indexed = 2; RGB = 3; CMYK = 4; Multichannel = 7; Duotone = 8; Lab = 9.
	int 		  mColourDataLen; //set to zero for non indexed or duotone images
	int 		  mResourceDataLen; //Set to zero
};

struct ResolutionInfo
{
	int hRes;              /* Fixed-point number: pixels per inch */
	short hResUnit;          /* 1=pixels per inch, 2=pixels per centimeter */
	short WidthUnit;         /* 1=in, 2=cm, 3=pt, 4=picas, 5=columns */
	int vRes;              /* Fixed-point number: pixels per inch */
	short vResUnit;          /* 1=pixels per inch, 2=pixels per centimeter */
	short HeightUnit;        /* 1=in, 2=cm, 3=pt, 4=picas, 5=columns */
};


struct DisplayInfo
{
	short  ColorSpace;
	short  Color[4];
	short  Opacity;          /* 0-100 */
	char   Kind;             /* 0=selected, 1=protected */
	char   Padding;          /* Always zero */
};

struct SImageResourceBlock
{
	char 		  mSIG[4];
	int 		  mID;
	unsigned char mNameSize;
	void deMot()
	{
		mID = IntelToMot16(mID);		
	}
};

struct PSDRecti
{
	//PSDRecti() :top(0), left(0), bottom(0), right(0){}
	int top, left, bottom, right;
};

struct Pix8pp
{
	unsigned char pix;
	unsigned char pix2;
	unsigned char alpha;
};


struct SChanImageData
{
	enum
	{
		CMPR_NONE = 0,
		CMPR_RLE = 1,
		CMPR_ZIP = 2,
		CMPR_ZIP_WITH_PREDICTION = 3,
	};
	unsigned short mCompression;	
};

struct SChanInfo
{
	unsigned short ID;
	unsigned int   mChannelDataLength;
	void toMot()
	{
		ID = IntelToMot16(ID);
		mChannelDataLength = IntelToMot32(mChannelDataLength);
	}

};

#pragma pack()

std::ostream& operator << (std::ostream& out, const SPSD_Header &data)
{
	out << "SIG:" << data.mSIG[0] << data.mSIG[1] << data.mSIG[2] << data.mSIG[3] << std::endl;
	out << "Ver:" << data.mVer << std::endl << "Reserved:" << data.mReserved << std::endl;
	out << "Chan:" << data.mChan << std::endl << "Height:" << data.mHeight << std::endl;
	out << "Width:" << data.mWidth << std::endl << "Depth:" << data.mDepth << std::endl << "Mode:" << data.mMode << std::endl << "ColourDataLen:" << data.mColourDataLen << std::endl << "ResourceDataLen:" << data.mResourceDataLen << std::endl;
	return out;
}

unsigned int makeEven(unsigned int v)
{
	unsigned int r = v += v & 1;
	if (r == 0) r = 2;
	return r;

}


void freadmem(void *data, size_t elem, size_t count, unsigned char **fdata)
{
	memcpy(data, *fdata, elem * count);
	*fdata += elem*count;
}

int getPSDInt(unsigned char**fdata)
{
	int val = IntelToMot32(*(int*)*fdata);
	*fdata += 4;
	return val;
}

int getPSDShort(unsigned char**fdata)
{
	short val = IntelToMot16(*(int*)*fdata);
	*fdata += 2;
	return val;
}

unsigned char getPSDchar(unsigned char **fdata)
{
	unsigned char val = **fdata;
	*fdata += 1;
	return val;
}

char getSignedPSDchar(unsigned char **fdata)
{
	char val = (char)**fdata;
	*fdata += 1;
	return val;
}

const std::string &getPSDString(unsigned char **fdata, std::string &string, bool pad)
{
	unsigned char stringLength = getPSDchar(fdata);	
	string = std::string((const char *)*fdata, stringLength);
	if (pad)
		stringLength += (stringLength & 3) - 1;
	*fdata += stringLength;
	return string;
}

const std::wstring &getPSDWString(unsigned char **fdata, std::wstring &string, bool pad)
{
	unsigned int stringLength = getPSDInt(fdata);
	string = std::wstring((const wchar_t *)*fdata, stringLength);
	if (pad)
		stringLength += (stringLength & 3) - 1;
	*fdata += stringLength * 2;
	return string;
}


PSDRecti getPSDRect(unsigned char **fptr)
{
	return{ getPSDInt(fptr), getPSDInt(fptr), getPSDInt(fptr), getPSDInt(fptr) };
}


size_t fsize(FILE *f)
{
	size_t fpos = ftell(f);
	fseek(f, 0, SEEK_END);
	size_t retme = ftell(f);
	fseek(f, fpos, SEEK_SET);
	return retme;
}

enum EPSBlendModes
{
	BM_PASS = 0x73736170,
	BM_NORM = 0x6d726f6e,
	BM_DISS = 0x73736964,
	BM_DARK = 0x6b726164,
	BM_MUL = 0x206c756d,
	BM_IDIV = 0x76696469,
	BM_LBRN = 0x6e72626c,
	BM_DKCL = 0x6c436b64,
	BM_LITE = 0x6574696c,
	BM_SCRN = 0x6e726373,
	BM_DIV = 0x20766964,
	BM_LDDG = 0x6764646c,
	BM_LGCL = 0x6c43676c,
	BM_OVER = 0x7265766f,
	BM_SLIT = 0x74694c73,
	BM_HLIT = 0x74694c68,
	BM_VLIT = 0x74694c76,
	BM_LLIT = 0x74694c6c,
	BM_PLIT = 0x74694c70,
	BM_HMIX = 0x78694d68,
	BM_DIFF = 0x66666964,
	BM_SMUD = 0x64756d73,
	BM_FSUB = 0x62757366,
	BM_FDIV = 0x76696466,
	BM_SAT = 0x20746173,
	BM_COLR = 0x726c6f63,
	BM_LUM = 0x6d756c
};

enum EPSLayerTypes
{
	BM_SOCO = 0x6f436f53,
	BM_GDFL = 0x6c466447,
	BM_PTFL = 0x6c467450,
	BM_BRIT = 0x74697262,
	BM_LEVL = 0x6c76656c,
	BM_CURV = 0x76727563,
	BM_EXPA = 0x41707865,
	BM_VIBA = 0x41626976,
	BM_HUE = 0x20657568,
	BM_HUE2 = 0x32657568,
	BM_BLNC = 0x636e6c62,
	BM_BLWH = 0x68776c62,
	BM_PHFL = 0x6c666870,
	BM_MIXR = 0x7278696d,
	BM_CLRL = 0x4c726c63,
	BM_NVRT = 0x7472766e,
	BM_POST = 0x74736f70,
	BM_THRS = 0x73726874,
	BM_GRDM = 0x6d647267,
	BM_SELC = 0x636c6573,
	BM_TYSH = 0x68537974,
	BM_LUNI = 0x696e756c,
	BM_LYID = 0x6469796c,
	BM_LFX2 = 0x3278666c,
	BM_PATT = 0x74746150,
	BM_ANNO = 0x6f6e6e41,
	BM_CLBL = 0x6c626c63,
	BM_INFX = 0x78666e69,
	BM_KNKO = 0x6f6b6e6b,
	BM_LSPF = 0x6670736c,
	BM_LCLR = 0x726c636c,
	BM_FXRP = 0x70727866,
	BM_LSCT = 0x7463736c,
	BM_BRST = 0x74737262,
	BM_VMSK = 0x6b736d76,
	BM_VSMS = 0x736d7376,
	BM_FFXI = 0x69786666,
	BM_LNSR = 0x72736e6c,
	BM_SHPA = 0x61706873,
	BM_SHMD = 0x646d6873,
	BM_LYVR = 0x7276796c,
	BM_TSLY = 0x796c7374,
	BM_LMGM = 0x6d676d6c,
	BM_VMGM = 0x6d676d76,
	BM_PLLD = 0x644c6c70,
	BM_LNKD = 0x446b6e6c,
	BM_CGED = 0x64456743,
	BM_TXT2 = 0x32747854,	
	BM_PTHS = 0x73687470,
	BM_ANFX = 0x58466e61,
	BM_FMSK = 0x6b734d46,
	BM_SOLD = 0x644c6f53,
	BM_VSTK = 0x6b747376,
	BM_VSCG = 0x67637376,
	BM_SN2P = 0x50326e73,
	BM_VOGK = 0x6b676f76,
	BM_MTRN = 0x6e72744d,
	BM_LMSK = 0x6b734d4c,	
	BM_FXID = 0x64695846
};

union UMaskInfo
{
	struct var1
	{
		unsigned char mDensity;
		double		  mMaskFeather;
		unsigned char mVectorMaskDensity;
		double		  mVectorMaskFeather;
	};
	struct var2
	{
		unsigned char mDensity;		
		unsigned char mVectorMaskDensity;
		double		  mVectorMaskFeather;
	};
	struct var3
	{
		unsigned char mDensity;
		double		  mMaskFeather;		
		double		  mVectorMaskFeather;
	};

};

struct SPSDLayer
{
	PSDRecti		bounds;
	short			chancount;
	SChanInfo	 *	ChanInfo;
	EPSBlendModes	blendMode;
	unsigned char	opacity;
	unsigned char	clipMode;
	unsigned char	layerFlags;
	PSDRecti		layerMaskRect;
	unsigned char	layerMaskDefaultColour;
	unsigned char	layerMaskFlags;
	int				compositeGreyBlendSource;
	int				compositeGreyBlendDest;
	unsigned int *	channelBlendsSource;
	unsigned int *	channelBlendsDests;
	std::string		mName;
};

size_t GetMaskInfoSizeFromFlags(unsigned int flags)
{
	size_t size = 0;
	if (flags & 0x1)
		size += 1;
	if (flags & 0x2)
		size += 8;
	if (flags & 0x3)
		size += 1;
	if (flags & 0x4)
		size += 8;
	return size;
}

bool checkSig(const char *SIG, const char *str)
{
	return (SIG[0] == str[0]) && (SIG[1] == str[1]) && (SIG[2] == str[2]) && (SIG[3] == str[3]);
} 

unsigned int roundUpToPowerOf2(unsigned int val)
{
	int i = 0;
	while ((1 << i) < val) ++i;
	return 1 << i;
}

void LoadPSD(const char *filename)
{
	SPSD_Header PSD;
	
	FILE *f = fopen( filename, "rb");
	size_t fsz = fsize(f);
	unsigned char *fileData = new unsigned char[fsz];
	unsigned char *fptr = fileData;
	fread(fileData, 1, fsz, f);
	fclose(f);
	size_t PSDs = sizeof(PSD);
	freadmem(&PSD, 1, sizeof(PSD), &fptr);

    std::cout << "Filename: " << filename << std::endl;
    PSD.deMot();
    std::cout << "got here 1" << std::endl;
    std::cout << PSD << std::endl;

	int offset = 0;
	const unsigned char *end = &fptr[PSD.mResourceDataLen];
	while (fptr < end)
	{
       	
		SImageResourceBlock *IRB = (SImageResourceBlock *)fptr;
    	
    	IRB->deMot();

    	int slen = makeEven(IRB->mNameSize);
		size_t srbs = sizeof(SImageResourceBlock);
		char *name = (char*)&fptr[srbs];
    	//std::cout << "Block SIG: " << IRB->mSIG[0] << IRB->mSIG[1] << IRB->mSIG[2] << IRB->mSIG[3] << std::endl;
    	std::cout << "Block ID: " << IRB->mID << std::endl;
    	std::cout << "Block name: " << name << std::endl;
    	name[slen] = 0;
		int datalen = 0;
		size_t rsize = sizeof(ResolutionInfo);
		fptr += sizeof(SImageResourceBlock);
						
		int offset = 0;
		while ((*fptr != '8') && (fptr[1] != 'B') && (fptr[2] != 'I') && (fptr[3] != 'M'))
		{			
			++fptr;
			++offset;
			if (fptr >= end)
				break;
		}
    }
	
	int layerandmaskinfosize = getPSDInt(&fptr);
	unsigned char *oldfptr = fptr;
	int olayerinfosize = getPSDInt(&fptr); //round up to nearest power of 2

	int layerinfosize = roundUpToPowerOf2(olayerinfosize);
	short layercount = getPSDShort(&fptr); //sanity check
	SPSDLayer *layers = new SPSDLayer[layercount];
	for (int i = 0; i < layercount; ++i)
	{
		SPSDLayer *cl = &layers[i];
		cl->bounds = getPSDRect(&fptr);
		//std::cout << "Layer dimemsions" << top << ", " << left << ", " << bottom << ", " << right << std::endl;

		cl->chancount = getPSDShort(&fptr);
		cl->ChanInfo = new SChanInfo[cl->chancount];
		
		for (int i = 0; i < cl->chancount; ++i)
		{
			freadmem(&cl->ChanInfo[i], sizeof(SChanInfo), 1, &fptr);
			cl->ChanInfo[i].toMot();
		}
		char sig[4];
		freadmem(sig, 1, 4, &fptr);
		if (!checkSig(sig, "8BIM"))
		{
			throw std::exception("Signature not found", 0);
		}
		
		freadmem(&cl->blendMode, 4, 1, &fptr);
		cl->opacity = getPSDchar(&fptr);
		cl->clipMode = getPSDchar(&fptr); //0 = base, 1 = non-base
		cl->layerFlags = getPSDchar(&fptr);
		getPSDchar(&fptr); //filler
		unsigned char *layeroldfptr = fptr;
		unsigned int dataBlockSize = getPSDInt(&fptr);
		
		unsigned int layerMaskDataSize = getPSDInt(&fptr);
		if (layerMaskDataSize > 0)
		{
			cl->layerMaskRect = getPSDRect(&fptr);
			cl->layerMaskDefaultColour = getPSDchar(&fptr);
			cl->layerMaskFlags = getPSDchar(&fptr);
			UMaskInfo maskInfo;
			freadmem(&maskInfo, GetMaskInfoSizeFromFlags(cl->layerMaskFlags), 1, &fptr);
			if (layerMaskDataSize == 20)
				fptr += 2;
			unsigned char realLayerMaskFlags = getPSDchar(&fptr);
			unsigned char realUserMaskBackground= getPSDchar(&fptr);
			PSDRecti enclosingRect = getPSDRect(&fptr);
		}
		unsigned int layerBlendingRangesData = getPSDInt(&fptr);
		if (layerBlendingRangesData > 0)
		{
			cl->compositeGreyBlendSource = getPSDInt(&fptr);
			cl->compositeGreyBlendDest = getPSDInt(&fptr);
			cl->channelBlendsSource = new unsigned int[cl->chancount];
			cl->channelBlendsDests = new unsigned int[cl->chancount];
			for (size_t i = 0; i < cl->chancount; ++i)
			{
				cl->channelBlendsSource[i] = getPSDInt(&fptr);
				cl->channelBlendsDests[i] = getPSDInt(&fptr);
			}
		}
		
		cl->mName = getPSDString(&fptr, cl->mName, true); 

		while ((checkSig((const char*)fptr, "8BIM") || (checkSig((const char*)fptr, "8B64"))))
		{	
			//found extra layer data
			fptr += 4;
			const char *data = (const char *)fptr;
			EPSLayerTypes layerType;
			freadmem(&layerType, 4, 1, &fptr);
			if (layerType = BM_LUNI)
			{
				std::wstring str;
				getPSDWString(&fptr, str, false);
			}
			int dataSize = getPSDInt(&fptr);			
		}
		fptr = layeroldfptr + dataBlockSize + 4;
		
	}
	SChanImageData imageData;
	SPSDLayer *cl = layers;
	for (int i = 0; i < layercount; ++i)
	{
		imageData.mCompression = getPSDShort(&fptr);
		
		size_t ysize = cl->bounds.bottom - cl->bounds.top;
		size_t xsize = cl->bounds.right - cl->bounds.left;
		unsigned char *imageData = new unsigned char[cl->chancount * cl->ChanInfo->mChannelDataLength * xsize * ysize];
		switch (imageData.mCompression)
		{
			case SChanImageData::CMPR_NONE:
			{
				
				break;
			};
			case SChanImageData::CMPR_RLE:
			{
				unsigned short *scaneLineByteCounts = new unsigned short[ysize];
				freadmem(scaneLineByteCounts, 2, ysize, &fptr);
				unsigned char *RLEScanlines = fptr;
				

				for (size_t i = 0; i < ysize; ++i)
				{
					int xpos = 0;
					while (xpos < xsize)
					{
						char code = getSignedPSDchar(&fptr);
						if (code == -128)
						{
							//next byte is header byte
						}
						else if (code < 0)
						{
							char data = getSignedPSDchar(&fptr);
							int count = 1 - code;


						}
						else 
					}
					RLEScanlines += scaneLineByteCounts[i];
				}
				break;
			};
			case SChanImageData::CMPR_ZIP:
			{
				break;
			};
			case SChanImageData::CMPR_ZIP_WITH_PREDICTION:
			{
				break;
			};
		}
		++cl;
	}

	fptr = oldfptr + layerandmaskinfosize;
	///IMAGE DATA
	
	imageData.mCompression = getPSDShort(&fptr);

	delete[] fileData;
}

void SavePSD(const char *filename)
{
	const int w = 256;
	const int h = 256;
	Pix8pp *pixels = new Pix8pp[w * h];

    SPSD_Header PSD(w,h);

    unsigned char* cpix = (unsigned char*)pixels;
    for (int y = 0; y < 256; y++)
        for (int x = 0; x < 256; x++)
        {
            cpix[0] = (x * 4) & 255;
            cpix[1] = (y * 4) & 255;
            cpix[2] = (x / 64) * 17 + (y / 64) * 68;
            cpix += 3;
        }
    
    FILE *f = fopen(filename, "wb");
    fwrite(&PSD, 1, sizeof(PSD), f);
    fwrite(pixels, sizeof(Pix8pp), w*h, f);
    fclose(f);
}

int main(int argc, char const *argv[])
{

	LoadPSD("C:\\Users\\Tim\\Pictures\\gimpsdtest.psd");
	SavePSD("C:\\Users\\Tim\\Pictures\\custompsd.psd");
	LoadPSD("C:\\Users\\Tim\\Pictures\\custompsd.psd");
	std::cout << IntelToMot16(1) << std::endl;
	return 0;
}