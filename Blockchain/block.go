package blockchain

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"time"
)

//取引データ格納用の構造体
type Transaction struct {
	Sender string
	Recepient string
	Timestamp time.Time
}

//ブロックチェーンのブロックの構造体
type Block struct {
	index int64
	timestamp time.Time
	transaction []Transaction
	prevHash string
	nonce int64
}

//ブロックのハッシュを生成する
func (b *Block) CreateHash() (string,error) {
	jsondata,err := json.Marshal(&b)
	if err != nil {
		return "",errors.New("can not create new block")
	}
	hashdata := sha256.Sum256(jsondata)
	return hex.EncodeToString(hashdata[:]),nil
}